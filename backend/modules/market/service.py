"""
Market data service — Yahoo Finance integration with BD-backed gap fill.

Design principles:
- BD is the single source of truth. Yahoo Finance is only the data provider.
- Gap fill: check MAX(price_date) per asset, download only the missing range.
- In-memory cache (TTL 5 min) to avoid repeated BD queries for current prices.
- If Yahoo is down: return last known BD price + is_stale=True flag.
- All writes are idempotent: ON CONFLICT (asset_id, price_date) DO NOTHING.
- Recovery: when Yahoo comes back after an outage, a single gap fill catches up all missing days.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

import pandas as pd
import yfinance as yf
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import AssetType, FetchStatus, ParameterKey
from modules.market.schemas import (
    AssetPriceHistoryResponse,
    AssetPriceOut,
    GapFillResponse,
    MarketPricesResponse,
    PriceHistoryPoint,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Stale thresholds (calendar days)
#  Equity/ETF: weekends (Sat+Sun) + 1-day holiday buffer  → 3 days
#  Crypto:     trades 24/7                                → 1 day
# ─────────────────────────────────────────────────────────────────────────────
_STALE_DAYS_EQUITY = 3
_STALE_DAYS_CRYPTO = 1

# ─────────────────────────────────────────────────────────────────────────────
#  In-memory price cache
# ─────────────────────────────────────────────────────────────────────────────
_CACHE_TTL_SECONDS = 300  # 5 minutes


@dataclass
class _PriceCache:
    prices: list[AssetPriceOut] = field(default_factory=list)
    fetched_at: float = 0.0  # time.monotonic() timestamp


_cache = _PriceCache()
_cache_lock: asyncio.Lock | None = None


def _get_cache_lock() -> asyncio.Lock:
    """Lazy initialization — asyncio.Lock must be created inside a running loop."""
    global _cache_lock
    if _cache_lock is None:
        _cache_lock = asyncio.Lock()
    return _cache_lock


# ─────────────────────────────────────────────────────────────────────────────
#  Default inception date (fallback when not in parameters table)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_INCEPTION = date(2020, 1, 1)

# Max rows per INSERT VALUES clause (avoids PostgreSQL parameter limit)
_INSERT_CHUNK_SIZE = 500


# ─────────────────────────────────────────────────────────────────────────────
#  Synchronous helpers — called via asyncio.to_thread to avoid blocking
# ─────────────────────────────────────────────────────────────────────────────

def _yf_download_batch(
    tickers: list[str],
    start: date,
    end: date,
) -> dict[str, pd.DataFrame]:
    """
    Download OHLCV data for a list of tickers from Yahoo Finance.

    Returns a dict {ticker: DataFrame} where each DataFrame has a DatetimeIndex
    (converted to date objects) and columns [Open, High, Low, Close, Volume].

    Raises on complete failure so the caller can fall back to per-ticker downloads.
    """
    start_str = start.isoformat()
    # yfinance's end date is exclusive, so add 1 day to include today's data
    end_str = (end + timedelta(days=1)).isoformat()

    logger.info("yf.download batch: %d tickers from %s to %s", len(tickers), start_str, end_str)

    raw = yf.download(
        tickers=tickers if len(tickers) > 1 else tickers[0],
        start=start_str,
        end=end_str,
        auto_adjust=True,   # adjusts for splits and dividends
        progress=False,
        threads=True,
    )

    if raw is None or raw.empty:
        return {}

    result: dict[str, pd.DataFrame] = {}

    if len(tickers) == 1:
        # Single-ticker download: flat columns [Open, High, Low, Close, Volume]
        ticker = tickers[0]
        df = _extract_ohlcv_single(raw)
        if df is not None and not df.empty:
            result[ticker] = df
    else:
        # Multi-ticker download: MultiIndex columns (Price, Ticker)
        # e.g., ('Close', 'IWDA.AS'), ('Open', 'IWDA.AS'), ...
        for ticker in tickers:
            df = _extract_ohlcv_multi(raw, ticker)
            if df is not None and not df.empty:
                result[ticker] = df

    return result


def _extract_ohlcv_single(raw: pd.DataFrame) -> pd.DataFrame | None:
    """Extract OHLCV from a single-ticker yfinance DataFrame.

    yfinance >= 1.0 always returns MultiIndex columns (Price, Ticker) even for
    single-ticker downloads. This function handles both the legacy flat format
    and the new MultiIndex format.
    """
    try:
        # yfinance 1.x: always MultiIndex (Price, Ticker)
        if isinstance(raw.columns, pd.MultiIndex):
            ticker_name = raw.columns.get_level_values(1)[0]
            return _extract_ohlcv_multi(raw, ticker_name)

        # Legacy flat columns: ["Open", "High", "Low", "Close", "Volume"]
        needed = {"Open", "High", "Low", "Close", "Volume"}
        if not needed.issubset(set(raw.columns)):
            return None
        df = raw[list(needed)].copy()
        df = df.dropna(subset=["Close"])
        df.index = pd.to_datetime(df.index).date
        return df
    except Exception as exc:
        logger.warning("_extract_ohlcv_single failed: %s", exc)
        return None


def _extract_ohlcv_multi(raw: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    """Extract OHLCV for a specific ticker from a multi-ticker yfinance DataFrame."""
    try:
        df = pd.DataFrame({
            "Open":   raw["Open"][ticker],
            "High":   raw["High"][ticker],
            "Low":    raw["Low"][ticker],
            "Close":  raw["Close"][ticker],
            "Volume": raw["Volume"][ticker],
        })
        df = df.dropna(subset=["Close"])
        df.index = pd.to_datetime(df.index).date
        return df
    except (KeyError, TypeError) as exc:
        logger.warning("_extract_ohlcv_multi failed for %s: %s", ticker, exc)
        return None


def _yf_download_single_with_retry(
    ticker: str,
    start: date,
    end: date,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Download a single ticker with exponential-backoff retry.
    Returns an empty DataFrame on complete failure (never raises).
    """
    start_str = start.isoformat()
    end_str = (end + timedelta(days=1)).isoformat()

    for attempt in range(1, max_retries + 1):
        try:
            raw = yf.download(
                tickers=ticker,
                start=start_str,
                end=end_str,
                auto_adjust=True,
                progress=False,
            )
            if raw is not None and not raw.empty:
                df = _extract_ohlcv_single(raw)
                if df is not None and not df.empty:
                    return df
        except Exception as exc:
            wait = 2 ** attempt
            logger.warning(
                "Attempt %d/%d for %s failed: %s — retrying in %ds",
                attempt, max_retries, ticker, exc, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

    logger.error("All %d attempts failed for %s", max_retries, ticker)
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
#  Gap fill — public API
# ─────────────────────────────────────────────────────────────────────────────

async def fill_all_gaps(db: AsyncSession) -> GapFillResponse:
    """
    For every active asset with a Yahoo Finance ticker:
      1. Find the last price date in BD (MAX price_date per asset).
      2. If no data exists, use the portfolio inception date from parameters.
      3. Download all missing days from Yahoo Finance in batches (grouped by start date).
      4. Insert idempotently — ON CONFLICT (asset_id, price_date) DO NOTHING.
      5. Log each operation to price_fetch_logs.
      6. Commit per ticker so partial success is persisted even on later failures.
    """
    t_start = time.monotonic()
    triggered_at = datetime.now()

    # ── 1. Fetch active assets with Yahoo tickers ─────────────────────────────
    assets_result = await db.execute(text("""
        SELECT id, ticker_yf, asset_type, currency, display_name
        FROM assets
        WHERE is_active = TRUE AND ticker_yf IS NOT NULL
        ORDER BY sort_order
    """))
    assets = assets_result.fetchall()

    if not assets:
        return GapFillResponse(
            rows_inserted=0,
            assets_updated=[],
            assets_failed=[],
            assets_skipped=[],
            duration_ms=0,
            errors=[],
            triggered_at=triggered_at,
        )

    asset_ids = [a.id for a in assets]
    # Map ticker_yf → asset metadata
    asset_by_ticker: dict[str, dict] = {
        a.ticker_yf: {
            "id": a.id,
            "asset_type": a.asset_type,
            "currency": a.currency,
            "display_name": a.display_name,
        }
        for a in assets
    }

    # ── 2. MAX(price_date) per asset in a single query ────────────────────────
    id_list = ",".join(str(i) for i in asset_ids)
    last_dates_result = await db.execute(text(f"""
        SELECT asset_id, MAX(price_date) AS last_date
        FROM price_history
        WHERE asset_id IN ({id_list})
        GROUP BY asset_id
    """))
    last_dates: dict[int, date] = {r.asset_id: r.last_date for r in last_dates_result}

    # ── 3. Portfolio inception date from parameters ───────────────────────────
    inception_row = await db.execute(
        text("SELECT value FROM parameters WHERE key = :key LIMIT 1"),
        {"key": ParameterKey.PORTFOLIO_INCEPTION_DATE},
    )
    inception_param = inception_row.scalar()
    try:
        inception_date = date.fromisoformat(inception_param) if inception_param else _DEFAULT_INCEPTION
    except (ValueError, TypeError):
        inception_date = _DEFAULT_INCEPTION

    today = date.today()

    # ── 4. Determine start date per ticker ───────────────────────────────────
    ticker_start: dict[str, date] = {}
    assets_skipped: list[str] = []

    for a in assets:
        last_date = last_dates.get(a.id)
        if last_date is None:
            start = inception_date
        else:
            start = last_date + timedelta(days=1)

        if start > today:
            assets_skipped.append(a.display_name)
            logger.debug("%s: up-to-date (last=%s)", a.ticker_yf, last_date)
        else:
            ticker_start[a.ticker_yf] = start

    if not ticker_start:
        return GapFillResponse(
            rows_inserted=0,
            assets_updated=[],
            assets_failed=[],
            assets_skipped=assets_skipped,
            duration_ms=int((time.monotonic() - t_start) * 1000),
            errors=[],
            triggered_at=triggered_at,
        )

    # ── 5. Group tickers by start date → batched yfinance download ────────────
    start_to_tickers: dict[date, list[str]] = defaultdict(list)
    for ticker, start in ticker_start.items():
        start_to_tickers[start].append(ticker)

    rows_inserted_total = 0
    assets_updated: list[str] = []
    assets_failed: list[str] = []
    all_errors: list[str] = []

    for start_date, tickers in sorted(start_to_tickers.items()):
        logger.info(
            "Gap fill batch: %d tickers from %s to %s — %s",
            len(tickers), start_date, today, tickers,
        )

        # Try batch download first; fall back to per-ticker on failure
        try:
            ticker_data = await asyncio.to_thread(
                _yf_download_batch, tickers, start_date, today
            )
        except Exception as exc:
            logger.warning("Batch download failed (%s); falling back to per-ticker", exc)
            ticker_data = {}

        # Retry individually any ticker that failed or was absent in batch
        missing_from_batch = set(tickers) - set(ticker_data.keys())
        for ticker in missing_from_batch:
            logger.info("Retrying individually: %s", ticker)
            try:
                df = await asyncio.to_thread(
                    _yf_download_single_with_retry, ticker, start_date, today
                )
                if not df.empty:
                    ticker_data[ticker] = df
                else:
                    err = f"{ticker}: no data returned by Yahoo Finance"
                    all_errors.append(err)
                    info = asset_by_ticker[ticker]
                    assets_failed.append(info["display_name"])
                    logger.warning(err)
                    await _log_fetch(db, info["id"], ticker, FetchStatus.FAILED, error=err)
                    await db.commit()
            except Exception as exc:
                err = f"{ticker}: download failed — {exc}"
                all_errors.append(err)
                info = asset_by_ticker[ticker]
                assets_failed.append(info["display_name"])
                logger.error(err)
                await _log_fetch(db, info["id"], ticker, FetchStatus.FAILED, error=err)
                await db.commit()

        # ── 6. Insert into price_history, one ticker at a time ────────────────
        for ticker, df in ticker_data.items():
            info = asset_by_ticker.get(ticker)
            if info is None:
                continue

            asset_id = info["id"]
            currency = info["currency"]
            display_name = info["display_name"]
            inserted_count = 0

            try:
                rows = _dataframe_to_rows(df, asset_id, currency)

                if not rows:
                    assets_skipped.append(display_name)
                    continue

                inserted_count = await _bulk_insert_price_history(db, rows)
                rows_inserted_total += inserted_count
                assets_updated.append(display_name)
                logger.info("%s (%s): inserted %d rows", display_name, ticker, inserted_count)

                last_price = float(df["Close"].iloc[-1]) if not df.empty else None
                await _log_fetch(db, asset_id, ticker, FetchStatus.SUCCESS, price=last_price)
                await db.commit()

            except Exception as exc:
                err = f"{display_name} ({ticker}): DB insert failed — {exc}"
                all_errors.append(err)
                assets_failed.append(display_name)
                logger.error(err)
                await db.rollback()
                await _log_fetch(db, asset_id, ticker, "failed", error=err)
                await db.commit()

    # Invalidate in-memory cache so next GET reflects new data
    lock = _get_cache_lock()
    async with lock:
        _cache.fetched_at = 0.0

    duration_ms = int((time.monotonic() - t_start) * 1000)
    logger.info(
        "Gap fill complete: %d rows in %dms | updated=%d, failed=%d, skipped=%d",
        rows_inserted_total, duration_ms,
        len(assets_updated), len(assets_failed), len(assets_skipped),
    )

    return GapFillResponse(
        rows_inserted=rows_inserted_total,
        assets_updated=sorted(set(assets_updated)),
        assets_failed=sorted(set(assets_failed)),
        assets_skipped=sorted(set(assets_skipped)),
        duration_ms=duration_ms,
        errors=all_errors,
        triggered_at=triggered_at,
    )


def _dataframe_to_rows(df: pd.DataFrame, asset_id: int, currency: str) -> list[dict]:
    """Convert a yfinance OHLCV DataFrame to a list of dicts ready for DB insert."""
    rows = []
    for price_date, row in df.iterrows():
        close_val = row.get("Close")
        if close_val is None or pd.isna(close_val):
            continue
        rows.append({
            "asset_id": asset_id,
            "price_date": price_date,
            "price_close": round(float(close_val), 4),
            "price_open":  round(float(row["Open"]), 4)   if not pd.isna(row.get("Open"))   else None,
            "price_high":  round(float(row["High"]), 4)   if not pd.isna(row.get("High"))   else None,
            "price_low":   round(float(row["Low"]), 4)    if not pd.isna(row.get("Low"))    else None,
            "volume":      int(row["Volume"])              if not pd.isna(row.get("Volume")) else None,
            "currency":    currency,
        })
    return rows


async def _bulk_insert_price_history(db: AsyncSession, rows: list[dict]) -> int:
    """
    INSERT rows into price_history in chunks with ON CONFLICT DO NOTHING.
    Returns total rows actually inserted.
    """
    inserted = 0
    for chunk_start in range(0, len(rows), _INSERT_CHUNK_SIZE):
        chunk = rows[chunk_start : chunk_start + _INSERT_CHUNK_SIZE]

        # Build parameterised VALUES clause
        value_placeholders = []
        params: dict = {}
        for i, r in enumerate(chunk):
            value_placeholders.append(
                f"(:ai{i},:pd{i},:pc{i},:po{i},:ph{i},:pl{i},:v{i},:cur{i})"
            )
            params[f"ai{i}"]  = r["asset_id"]
            params[f"pd{i}"]  = r["price_date"]
            params[f"pc{i}"]  = r["price_close"]
            params[f"po{i}"]  = r["price_open"]
            params[f"ph{i}"]  = r["price_high"]
            params[f"pl{i}"]  = r["price_low"]
            params[f"v{i}"]   = r["volume"]
            params[f"cur{i}"] = r["currency"]

        stmt = text(
            "INSERT INTO price_history "
            "(asset_id, price_date, price_close, price_open, price_high, price_low, volume, currency) "
            f"VALUES {','.join(value_placeholders)} "
            "ON CONFLICT (asset_id, price_date) DO NOTHING"
        )
        result = await db.execute(stmt, params)
        inserted += result.rowcount

    return inserted


async def _log_fetch(
    db: AsyncSession,
    asset_id: int,
    ticker: str,
    status: str,
    price: Optional[float] = None,
    error: Optional[str] = None,
    response_time_ms: Optional[int] = None,
) -> None:
    """Write a row to price_fetch_logs. Best-effort — swallows exceptions."""
    try:
        await db.execute(text("""
            INSERT INTO price_fetch_logs
                (asset_id, ticker, status, price_returned, error_message, response_time_ms)
            VALUES (:asset_id, :ticker, :status, :price, :error, :rtms)
        """), {
            "asset_id": asset_id,
            "ticker": ticker,
            "status": status,
            "price": price,
            "error": error,
            "rtms": response_time_ms,
        })
    except Exception as exc:
        logger.warning("Failed to write price_fetch_log for %s: %s", ticker, exc)


# ─────────────────────────────────────────────────────────────────────────────
#  Current prices — public API
# ─────────────────────────────────────────────────────────────────────────────

async def get_current_prices(db: AsyncSession) -> MarketPricesResponse:
    """
    Return the most recent known price for every active asset.

    Uses a window function (ROW_NUMBER PARTITION BY asset_id ORDER BY price_date DESC)
    to get the last 2 rows per asset, enabling 1-day change calculation.
    Results are cached in memory for _CACHE_TTL_SECONDS seconds.
    """
    lock = _get_cache_lock()
    async with lock:
        age = time.monotonic() - _cache.fetched_at
        if _cache.prices and age < _CACHE_TTL_SECONDS:
            return _build_market_response(_cache.prices, cached=True, cache_age=int(age))

    prices = await _query_current_prices(db)

    async with lock:
        _cache.prices = prices
        _cache.fetched_at = time.monotonic()

    return _build_market_response(prices, cached=False, cache_age=0)


async def _query_current_prices(db: AsyncSession) -> list[AssetPriceOut]:
    """Execute the window-function query and build AssetPriceOut objects."""
    rows = await db.execute(text("""
        WITH ranked AS (
            SELECT
                ph.asset_id,
                ph.price_date,
                ph.price_close,
                a.display_name,
                a.ticker_yf,
                a.asset_type,
                a.currency,
                ROW_NUMBER() OVER (
                    PARTITION BY ph.asset_id ORDER BY ph.price_date DESC
                ) AS rn
            FROM price_history ph
            JOIN assets a ON a.id = ph.asset_id
            WHERE a.is_active = TRUE
        ),
        latest AS (SELECT * FROM ranked WHERE rn = 1),
        prev   AS (SELECT asset_id, price_close AS prev_close FROM ranked WHERE rn = 2)
        SELECT
            l.asset_id,
            l.display_name,
            l.ticker_yf,
            l.asset_type,
            l.currency,
            l.price_close,
            l.price_date,
            p.prev_close
        FROM latest l
        LEFT JOIN prev p ON p.asset_id = l.asset_id
        ORDER BY l.display_name
    """))
    db_rows = rows.fetchall()
    priced_ids = {r.asset_id for r in db_rows}

    # Assets with no price data at all
    no_price_result = await db.execute(text("""
        SELECT id, display_name, ticker_yf, asset_type, currency
        FROM assets
        WHERE is_active = TRUE AND id NOT IN (
            SELECT DISTINCT asset_id FROM price_history
        )
    """))
    no_price_assets = no_price_result.fetchall()

    today = date.today()
    prices: list[AssetPriceOut] = []

    for row in db_rows:
        stale_days = (today - row.price_date).days if row.price_date else 9999
        stale_threshold = _STALE_DAYS_CRYPTO if row.asset_type == AssetType.CRYPTO else _STALE_DAYS_EQUITY
        is_stale = stale_days > stale_threshold

        change_pct_1d: Optional[Decimal] = None
        change_eur_1d: Optional[Decimal] = None
        if row.prev_close and row.price_close and float(row.prev_close) > 0:
            diff = float(row.price_close) - float(row.prev_close)
            change_pct_1d = Decimal(str(round(diff / float(row.prev_close) * 100, 4)))
            change_eur_1d = Decimal(str(round(diff, 4)))

        prices.append(AssetPriceOut(
            asset_id=row.asset_id,
            display_name=row.display_name,
            ticker_yf=row.ticker_yf,
            asset_type=row.asset_type,
            price_close=Decimal(str(row.price_close)) if row.price_close is not None else None,
            price_date=row.price_date,
            currency=row.currency,
            is_stale=is_stale,
            stale_days=stale_days,
            change_pct_1d=change_pct_1d,
            change_eur_1d=change_eur_1d,
        ))

    for asset in no_price_assets:
        prices.append(AssetPriceOut(
            asset_id=asset.id,
            display_name=asset.display_name,
            ticker_yf=asset.ticker_yf,
            asset_type=asset.asset_type,
            price_close=None,
            price_date=None,
            currency=asset.currency,
            is_stale=True,
            stale_days=9999,
            change_pct_1d=None,
            change_eur_1d=None,
        ))

    return sorted(prices, key=lambda p: p.display_name)


def _build_market_response(
    prices: list[AssetPriceOut],
    *,
    cached: bool,
    cache_age: int,
) -> MarketPricesResponse:
    fresh = sum(1 for p in prices if p.price_close is not None and not p.is_stale)
    stale = sum(1 for p in prices if p.price_close is not None and p.is_stale)
    no_data = sum(1 for p in prices if p.price_close is None)
    return MarketPricesResponse(
        prices=prices,
        total_assets=len(prices),
        fresh_count=fresh,
        stale_count=stale,
        no_data_count=no_data,
        cached=cached,
        cache_age_seconds=cache_age if cached else None,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Price history for charts — public API
# ─────────────────────────────────────────────────────────────────────────────

async def get_asset_price_history(
    db: AsyncSession,
    asset_id: int,
    days: int = 30,
) -> AssetPriceHistoryResponse | None:
    """
    Return OHLCV history for a single asset (most recent N calendar days).
    Returns None if the asset does not exist.
    """
    # Validate asset exists
    asset_row = await db.execute(text("""
        SELECT id, display_name, ticker_yf, currency
        FROM assets
        WHERE id = :asset_id AND is_active = TRUE
    """), {"asset_id": asset_id})
    asset = asset_row.fetchone()
    if asset is None:
        return None

    since = date.today() - timedelta(days=days)
    rows = await db.execute(text("""
        SELECT
            ph.price_date,
            ph.price_close,
            ph.price_open,
            ph.price_high,
            ph.price_low,
            ph.volume,
            LAG(ph.price_close) OVER (ORDER BY ph.price_date) AS prev_close
        FROM price_history ph
        WHERE ph.asset_id = :asset_id AND ph.price_date >= :since
        ORDER BY ph.price_date ASC
    """), {"asset_id": asset_id, "since": since})

    points: list[PriceHistoryPoint] = []
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    for row in rows:
        change_pct = None
        if row.prev_close and float(row.prev_close) > 0:
            change_pct = Decimal(str(round(
                (float(row.price_close) - float(row.prev_close)) / float(row.prev_close) * 100, 4
            )))

        point = PriceHistoryPoint(
            price_date=row.price_date,
            price_close=Decimal(str(row.price_close)),
            price_open=Decimal(str(row.price_open)) if row.price_open is not None else None,
            price_high=Decimal(str(row.price_high)) if row.price_high is not None else None,
            price_low=Decimal(str(row.price_low)) if row.price_low is not None else None,
            volume=Decimal(str(int(row.volume))) if row.volume is not None else None,
            change_pct=change_pct,
        )
        points.append(point)

        if from_date is None:
            from_date = row.price_date
        to_date = row.price_date

    return AssetPriceHistoryResponse(
        asset_id=asset.id,
        display_name=asset.display_name,
        ticker_yf=asset.ticker_yf,
        currency=asset.currency,
        data=points,
        from_date=from_date,
        to_date=to_date,
        total_rows=len(points),
    )
