import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HeroValue } from './HeroValue';

describe('HeroValue', () => {
  it('mostra el label PATRIMONI TOTAL', () => {
    render(<HeroValue total={23862.98} changeEur={1713.54} changePct={7.74} period="1A" />);
    expect(screen.getByText(/patrimoni total/i)).toBeInTheDocument();
  });

  it('mostra el valor formatat en EUR', () => {
    render(<HeroValue total={23862.98} changeEur={1713.54} changePct={7.74} period="1A" />);
    // Format ca-ES: 23.862,98
    expect(screen.getByText(/23\.862/)).toBeInTheDocument();
  });

  it('mostra triangle ▲ per canvi positiu', () => {
    render(<HeroValue total={23862.98} changeEur={1713.54} changePct={7.74} period="1A" />);
    expect(document.body.textContent).toContain('▲');
  });

  it('mostra triangle ▼ per canvi negatiu', () => {
    render(<HeroValue total={23862.98} changeEur={-500} changePct={-2.1} period="1A" />);
    // ▼ és un text node dins d'un span amb altres fills — usem textContent
    expect(document.body.textContent).toContain('▼');
  });

  it('mostra el percentatge de canvi', () => {
    render(<HeroValue total={23862.98} changeEur={1713.54} changePct={7.74} period="1A" />);
    expect(screen.getByText(/7\.74/)).toBeInTheDocument();
  });

  it('no peta amb canvi zero', () => {
    expect(() =>
      render(<HeroValue total={23862.98} changeEur={0} changePct={0} period="1A" />)
    ).not.toThrow();
  });
});
