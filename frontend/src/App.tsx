import { Routes, Route } from 'react-router-dom';
import { NavBar } from './components/ui/NavBar';
import { DashboardScreen } from './features/dashboard/DashboardScreen';
import { PortfolioScreen } from './features/portfolio/PortfolioScreen';

function PlaceholderScreen({ title }: { title: string }) {
  return (
    <div
      style={{
        background: 'var(--color-bg)',
        minHeight: '100vh',
        fontFamily: 'var(--font-body)',
        color: 'var(--color-text)',
        maxWidth: 430,
        margin: '0 auto',
        paddingBottom: 88,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
      }}
    >
      <div
        style={{
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: '-0.02em',
          fontFamily: 'var(--font-display)',
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 13,
          color: 'var(--color-text-tertiary)',
          fontFamily: 'var(--font-num)',
        }}
      >
        Pròximament
      </div>
    </div>
  );
}

export default function App() {
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
          <Route path="/" element={<DashboardScreen />} />
          <Route path="/portfolio" element={<PortfolioScreen />} />
          <Route
            path="/simulation"
            element={<PlaceholderScreen title="Simulació" />}
          />
          <Route
            path="/history"
            element={<PlaceholderScreen title="Historial" />}
          />
          <Route
            path="/settings"
            element={<PlaceholderScreen title="Configuració" />}
          />
        </Routes>
      </div>
      <NavBar />
    </>
  );
}
