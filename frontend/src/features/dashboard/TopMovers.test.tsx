import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TopMovers } from './TopMovers';
import type { AssetPrice } from '../../types';

const makePrices = (overrides: Partial<AssetPrice>[] = []): AssetPrice[] =>
  overrides.map((o, i) => ({
    asset_id: i + 1,
    display_name: `Asset ${i + 1}`,
    ticker_yf: 'IWDA.AS',
    asset_type: 'etf',
    price_close: '100.00',
    price_date: '2026-03-27',
    currency: 'EUR',
    is_stale: false,
    stale_days: 0,
    change_pct_1d: '1.5',
    change_eur_1d: '1.50',
    ...o,
  }));

describe('TopMovers', () => {
  it('shows empty state when no prices provided', () => {
    render(<TopMovers prices={[]} />);
    expect(screen.getByText(/sense dades/i)).toBeInTheDocument();
  });

  it('renders up to 4 assets', () => {
    const prices = makePrices([
      { display_name: 'MSCI World', change_pct_1d: '1.2' },
      { display_name: 'Bitcoin', change_pct_1d: '-3.3', ticker_yf: 'BTC-EUR' },
      { display_name: 'Physical Gold', change_pct_1d: '0.4', ticker_yf: 'PPFB.DE' },
      { display_name: 'MSCI Europe', change_pct_1d: '-0.3', ticker_yf: 'IMAE.AS' },
      { display_name: 'Japan', change_pct_1d: '1.5', ticker_yf: 'CSJP.AS' },
    ]);
    render(<TopMovers prices={prices} />);
    // Should show the 4 with highest absolute change, not all 5
    const items = screen.getAllByText(/Asset \d|MSCI World|Bitcoin|Physical Gold|MSCI Europe|Japan/);
    expect(items.length).toBeLessThanOrEqual(4);
  });

  it('sorts by absolute change (largest first)', () => {
    const prices = makePrices([
      { display_name: 'Small mover', change_pct_1d: '0.1' },
      { display_name: 'Big mover', change_pct_1d: '-5.0' },
    ]);
    render(<TopMovers prices={prices} />);
    const items = screen.getAllByText(/Small mover|Big mover/);
    // Big mover should appear first
    expect(items[0].textContent).toContain('Big mover');
  });

  it('shows positive change with + sign', () => {
    render(<TopMovers prices={makePrices([{ change_pct_1d: '2.50' }])} />);
    expect(screen.getByText(/\+2\.50%/)).toBeInTheDocument();
  });

  it('shows negative change without + sign', () => {
    render(<TopMovers prices={makePrices([{ change_pct_1d: '-1.80' }])} />);
    expect(screen.getByText(/-1\.80%/)).toBeInTheDocument();
  });

  it('shows "antic" badge for stale prices', () => {
    render(<TopMovers prices={makePrices([{ is_stale: true, change_pct_1d: '1.0' }])} />);
    expect(screen.getByText('antic')).toBeInTheDocument();
  });

  it('filters out assets with no price data', () => {
    const prices = makePrices([
      { display_name: 'No price asset', price_close: null },
      { display_name: 'Valid asset', price_close: '100.00' },
    ]);
    render(<TopMovers prices={prices} />);
    expect(screen.queryByText('No price asset')).not.toBeInTheDocument();
    expect(screen.getByText('Valid asset')).toBeInTheDocument();
  });
});
