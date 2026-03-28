import { useState, useEffect, useCallback } from 'react';

type AuthState = 'loading' | 'authenticated' | 'unauthenticated';

export function useAuth() {
  const [state, setState] = useState<AuthState>('loading');

  // Comprova l'estat de sessió en muntar el component
  useEffect(() => {
    fetch('/api/v1/auth/status', { credentials: 'same-origin' })
      .then((r) => setState(r.ok ? 'authenticated' : 'unauthenticated'))
      .catch(() => setState('unauthenticated'));
  }, []);

  // Captura events d'expiració de cookie emesos per api.ts
  useEffect(() => {
    const handle = () => setState('unauthenticated');
    window.addEventListener('auth:unauthorized', handle);
    return () => window.removeEventListener('auth:unauthorized', handle);
  }, []);

  const login = useCallback(async (password: string): Promise<string | null> => {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        setState('authenticated');
        return null; // sense error
      }
      return 'Contrasenya incorrecta';
    } catch {
      return 'Error de connexió';
    }
  }, []);

  return { state, login };
}
