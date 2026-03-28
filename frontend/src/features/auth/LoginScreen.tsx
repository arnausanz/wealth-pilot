import { useState, useRef, useEffect } from 'react';

interface LoginScreenProps {
  onLogin: (password: string) => Promise<string | null>;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Petit delay per deixar que el teclat d'iOS aparegui correctament
    const t = setTimeout(() => inputRef.current?.focus(), 300);
    return () => clearTimeout(t);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password) return;
    setLoading(true);
    setError('');
    const err = await onLogin(password);
    setLoading(false);
    if (err) {
      setError(err);
      setPassword('');
      inputRef.current?.focus();
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'var(--color-bg)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-body)',
        padding: '0 32px',
        zIndex: 1000,
      }}
    >
      {/* Logo / títol */}
      <div style={{ marginBottom: 40, textAlign: 'center' }}>
        <div
          style={{
            fontSize: 13,
            fontFamily: 'var(--font-num)',
            letterSpacing: '0.25em',
            color: 'var(--color-accent)',
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          WealthPilot
        </div>
        <div
          style={{
            fontSize: 28,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            fontFamily: 'var(--font-display)',
            color: 'var(--color-text)',
            lineHeight: 1.1,
          }}
        >
          Benvingut
        </div>
        <div
          style={{
            fontSize: 14,
            color: 'var(--color-text-tertiary)',
            marginTop: 6,
            fontFamily: 'var(--font-num)',
          }}
        >
          Introdueix la teva contrasenya
        </div>
      </div>

      {/* Formulari — atributs autocomplete per a iCloud Keychain */}
      <form
        onSubmit={handleSubmit}
        style={{ width: '100%', maxWidth: 320 }}
        autoComplete="on"
      >
        {/*
          Camp d'usuari ocult però present al DOM — necessari perquè
          iCloud Keychain i gestors de contrasenyes associïn la credencial
          correctament al domini.
        */}
        <input
          type="text"
          name="username"
          autoComplete="username"
          defaultValue="arnau"
          style={{ display: 'none' }}
          readOnly
          tabIndex={-1}
          aria-hidden="true"
        />

        <div
          style={{
            background: 'var(--color-glass-bg)',
            backdropFilter: 'var(--glass-blur)',
            WebkitBackdropFilter: 'var(--glass-blur)',
            border: `1px solid ${error ? 'var(--color-negative)' : 'var(--color-glass-border)'}`,
            borderRadius: 16,
            padding: '0 16px',
            boxShadow: 'var(--card-shadow)',
            transition: 'border-color 0.2s',
          }}
        >
          <input
            ref={inputRef}
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setError(''); }}
            placeholder="Contrasenya"
            disabled={loading}
            style={{
              width: '100%',
              padding: '18px 0',
              background: 'none',
              border: 'none',
              outline: 'none',
              fontSize: 17,
              fontFamily: 'var(--font-body)',
              color: 'var(--color-text)',
              caretColor: 'var(--color-accent)',
            }}
          />
        </div>

        {/* Missatge d'error */}
        {error && (
          <div
            style={{
              marginTop: 8,
              fontSize: 12,
              color: 'var(--color-negative)',
              fontFamily: 'var(--font-num)',
              textAlign: 'center',
              animation: 'slideDown 0.2s ease',
            }}
          >
            {error}
          </div>
        )}

        {/* Botó */}
        <button
          type="submit"
          disabled={loading || !password}
          style={{
            width: '100%',
            marginTop: 16,
            padding: '16px 0',
            borderRadius: 14,
            background: loading || !password
              ? 'var(--color-glass-border)'
              : 'var(--color-accent)',
            border: 'none',
            color: loading || !password ? 'var(--color-text-tertiary)' : '#fff',
            fontSize: 15,
            fontWeight: 600,
            fontFamily: 'var(--font-body)',
            cursor: loading || !password ? 'default' : 'pointer',
            transition: 'all 0.2s ease',
            letterSpacing: '0.01em',
          }}
        >
          {loading ? 'Verificant…' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
