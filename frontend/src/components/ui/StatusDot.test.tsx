import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { StatusDot } from './StatusDot';

describe('StatusDot', () => {
  it.each(['green', 'yellow', 'red'] as const)('renders without error for status "%s"', (status) => {
    const { container } = render(<StatusDot status={status} />);
    expect(container.firstChild).toBeTruthy();
  });

  it('applies correct CSS variable for green', () => {
    const { container } = render(<StatusDot status="green" />);
    const dot = container.firstChild as HTMLElement;
    expect(dot.style.background).toContain('var(--color-positive)');
  });

  it('applies correct CSS variable for red', () => {
    const { container } = render(<StatusDot status="red" />);
    const dot = container.firstChild as HTMLElement;
    expect(dot.style.background).toContain('var(--color-negative)');
  });

  it('applies correct CSS variable for yellow', () => {
    const { container } = render(<StatusDot status="yellow" />);
    const dot = container.firstChild as HTMLElement;
    expect(dot.style.background).toContain('var(--color-warning)');
  });
});
