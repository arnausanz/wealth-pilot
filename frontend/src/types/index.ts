// ─── Backend retorna Decimal com a string ──────────────────────────────────
// Tots els camps numèrics de l'API arriben com a string.
// Usa parseFloat() o el helper n() per convertir-los.
export const n = (v: string | number | null | undefined): number =>
  v == null ? 0 : typeof v === 'number' ? v : parseFloat(v) || 0;

// ─── Net Worth ──────────────────────────────────────────────────────────────

export interface AssetSnapshot {
  asset_id: number;
  display_name: string;
  ticker_yf: string;
  shares: string | number;
  price_eur: string | number;
  value_eur: string | number;
  cost_basis_eur: string | number;
  pnl_eur: string | number;
  pnl_pct: string | number;
  color_hex?: string;
}

export interface NetWorthSnapshot {
  id: number;
  snapshot_date: string;                        // "YYYY-MM-DD"
  total_net_worth: string | number;
  investment_portfolio_value: string | number;  // inv_value backend field
  cash_and_bank_value: string | number;         // cash_value backend field
  real_estate_value: string | number;
  pension_value: string | number;
  other_assets_value: string | number;
  total_liabilities: string | number;
  change_eur: string | number;
  change_pct: string | number;
  trigger_source: string;
  created_at: string;
  asset_snapshots: AssetSnapshot[];
}

export interface NetWorthHistoryResponse {
  snapshots: NetWorthSnapshot[];
  period: string;
  current_net_worth: string | number;
  change_eur_period: string | number;
  change_pct_period: string | number;
}

// ─── Market Prices ──────────────────────────────────────────────────────────

export interface AssetPrice {
  asset_id: number;
  display_name: string;
  ticker_yf: string;
  asset_type: string;
  price_close: string | number | null;
  price_date: string | null;
  currency: string;
  is_stale: boolean;
  stale_days: number;
  change_pct_1d: string | number | null;
  change_eur_1d: string | number | null;
}

export interface MarketPricesResponse {
  prices: AssetPrice[];
  total_assets: number;
  fresh_count: number;
  stale_count: number;
  no_data_count: number;
  cached: boolean;
  cache_age_seconds: number | null;
}

// ─── Asset colors (per ticker_yf) ──────────────────────────────────────────
export const ASSET_COLORS: Record<string, string> = {
  'IWDA.AS': '#3B82F6',
  'PPFB.DE': '#F59E0B',
  'IMAE.AS': '#8B5CF6',
  'EMIM.AS': '#06B6D4',
  'CSJP.AS': '#10B981',
  'WDEF.MI': '#F97316',
  'BTC-EUR': '#E11D48',
};

export const ASSET_COLOR_DEFAULT = '#64748B';
