import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from './Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>contingut de la card</Card>);
    expect(screen.getByText('contingut de la card')).toBeInTheDocument();
  });

  it('applies default padding of 14', () => {
    const { container } = render(<Card>test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.style.padding).toBe('14px');
  });

  it('respects custom padding prop', () => {
    const { container } = render(<Card padding={20}>test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.style.padding).toBe('20px');
  });

  it('merges custom style prop', () => {
    const { container } = render(<Card style={{ marginTop: '10px' }}>test</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.style.marginTop).toBe('10px');
  });

  it('forwards className', () => {
    const { container } = render(<Card className="my-class">test</Card>);
    expect(container.firstChild).toHaveClass('my-class');
  });
});
