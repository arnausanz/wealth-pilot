import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useThemeStore } from './useTheme';

// Mock window.matchMedia
beforeEach(() => {
  document.documentElement.classList.remove('dark');
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
  // Reset store to light
  useThemeStore.setState({ isDark: false });
});

describe('useThemeStore', () => {
  it('starts as light by default (store reset)', () => {
    const { result } = renderHook(() => useThemeStore());
    expect(result.current.isDark).toBe(false);
  });

  it('toggle switches light → dark', () => {
    const { result } = renderHook(() => useThemeStore());
    act(() => { result.current.toggle(); });
    expect(result.current.isDark).toBe(true);
  });

  it('toggle switches dark → light', () => {
    useThemeStore.setState({ isDark: true });
    const { result } = renderHook(() => useThemeStore());
    act(() => { result.current.toggle(); });
    expect(result.current.isDark).toBe(false);
  });

  it('setDark(true) adds "dark" class to <html>', () => {
    const { result } = renderHook(() => useThemeStore());
    act(() => { result.current.setDark(true); });
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('setDark(false) removes "dark" class from <html>', () => {
    document.documentElement.classList.add('dark');
    const { result } = renderHook(() => useThemeStore());
    act(() => { result.current.setDark(false); });
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('toggle also updates <html> class', () => {
    useThemeStore.setState({ isDark: false });
    const { result } = renderHook(() => useThemeStore());
    act(() => { result.current.toggle(); });
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    act(() => { result.current.toggle(); });
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
