import '@testing-library/jest-dom';
import { vi } from 'vitest';

// window.matchMedia no existeix a jsdom — cal mocar-ho AQUÍ perquè
// useTheme.ts el crida a nivell de mòdul (fora de hooks/components)
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
