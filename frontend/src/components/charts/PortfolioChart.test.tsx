import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { PortfolioChart } from './PortfolioChart';

// requestAnimationFrame en jsdom no existeix — mockegem sense cridar callback
// per evitar bucle infinit en l'animació de morphing
beforeEach(() => {
  vi.stubGlobal('requestAnimationFrame', (_cb: FrameRequestCallback) => 0);
  vi.stubGlobal('cancelAnimationFrame', (_id: number) => {});
});

const DATA = [10000, 10200, 10150, 10400, 10350, 10600, 10800, 11000, 10900, 11200];

describe('PortfolioChart', () => {
  it('renderitza un element SVG', () => {
    const { container } = render(<PortfolioChart data={DATA} />);
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('renderitza almenys un path (la línia)', () => {
    const { container } = render(<PortfolioChart data={DATA} />);
    expect(container.querySelectorAll('path').length).toBeGreaterThanOrEqual(1);
  });

  it('renderitza el cercle del punt final', () => {
    const { container } = render(<PortfolioChart data={DATA} />);
    expect(container.querySelectorAll('circle').length).toBeGreaterThanOrEqual(1);
  });

  it('renderitza les grid lines (almenys 3)', () => {
    const { container } = render(<PortfolioChart data={DATA} />);
    expect(container.querySelectorAll('line').length).toBeGreaterThanOrEqual(3);
  });

  it('no peta amb dades buides', () => {
    expect(() => render(<PortfolioChart data={[]} />)).not.toThrow();
  });

  it('no peta amb un sol punt', () => {
    expect(() => render(<PortfolioChart data={[15000]} />)).not.toThrow();
  });

  it('accepta width i height personalitzats', () => {
    const { container } = render(<PortfolioChart data={DATA} width={300} height={120} />);
    expect(container.querySelector('svg')).toBeTruthy();
  });
});
