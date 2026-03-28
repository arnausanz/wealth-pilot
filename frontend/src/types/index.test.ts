import { describe, it, expect } from 'vitest';
import { n, ASSET_COLORS } from './index';

describe('n() — Decimal string to number helper', () => {
  it('converts a string number', () => {
    expect(n('23862.98')).toBeCloseTo(23862.98);
  });

  it('converts a negative string', () => {
    expect(n('-1713.54')).toBeCloseTo(-1713.54);
  });

  it('returns 0 for null', () => {
    expect(n(null)).toBe(0);
  });

  it('returns 0 for undefined', () => {
    expect(n(undefined)).toBe(0);
  });

  it('returns 0 for empty string', () => {
    expect(n('')).toBe(0);
  });

  it('passes through a number unchanged', () => {
    expect(n(42.5)).toBeCloseTo(42.5);
  });

  it('handles "0.00" correctly', () => {
    expect(n('0.00')).toBe(0);
  });

  it('handles high-precision Decimal strings from backend', () => {
    expect(n('7.7400')).toBeCloseTo(7.74);
    expect(n('0.9500')).toBeCloseTo(0.95);
  });
});

describe('ASSET_COLORS', () => {
  it('contains all 7 portfolio assets', () => {
    const expectedTickers = ['IWDA.AS', 'PPFB.DE', 'IMAE.AS', 'EMIM.AS', 'CSJP.AS', 'WDEF.MI', 'BTC-EUR'];
    for (const ticker of expectedTickers) {
      expect(ASSET_COLORS).toHaveProperty(ticker);
    }
  });

  it('all colors are valid hex', () => {
    for (const color of Object.values(ASSET_COLORS)) {
      expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});
