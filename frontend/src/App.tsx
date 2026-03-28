import { Routes, Route } from 'react-router-dom';
import { NavBar } from './components/ui/NavBar';
import { DashboardScreen } from './features/dashboard/DashboardScreen';
import { PortfolioScreen } from './features/portfolio/PortfolioScreen';
import { SimulationScreen } from './features/simulation/SimulationScreen';
import { HistoryScreen } from './features/history/HistoryScreen';
import { SettingsScreen } from './features/settings/SettingsScreen';
import { AnalyticsScreen } from './features/analytics/AnalyticsScreen';
import { LoginScreen } from './features/auth/LoginScreen';
import { useAuth } from './hooks/useAuth';

export default function App() {
  const { state, login } = useAuth();

  // Pantalla de càrrega mentre es comprova la sessió
  if (state === 'loading') {
    return (
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background: 'var(--color-bg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            fontSize: 13,
            fontFamily: 'var(--font-num)',
            letterSpacing: '0.2em',
            color: 'var(--color-text-tertiary)',
            textTransform: 'uppercase',
            animation: 'pulse 1.5s ease infinite',
          }}
        >
          WealthPilot
        </div>
      </div>
    );
  }

  // Pantalla de login si no autenticat
  if (state === 'unauthenticated') {
    return <LoginScreen onLogin={login} />;
  }

  // App principal
  return (
    <>
      <div
        style={{
          maxWidth: 430,
          margin: '0 auto',
          minHeight: '100vh',
          position: 'relative',
        }}
      >
        <Routes>
          <Route path="/"          element={<DashboardScreen />} />
          <Route path="/portfolio" element={<PortfolioScreen />} />
          <Route path="/simulation" element={<SimulationScreen />} />
          <Route path="/history"   element={<HistoryScreen />} />
          <Route path="/settings"  element={<SettingsScreen />} />
          <Route path="/analytics" element={<AnalyticsScreen />} />
        </Routes>
      </div>
      <NavBar />
    </>
  );
}
