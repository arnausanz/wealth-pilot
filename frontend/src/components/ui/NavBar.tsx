import { useLocation, useNavigate } from 'react-router-dom';
import { HomeIcon, PortfolioIcon, ChartIcon, ListIcon, GearIcon, AnalyticsIcon } from '../icons/Icons';

const NAV_ITEMS = [
  { icon: 'home',      label: 'Inici',     path: '/' },
  { icon: 'portfolio', label: 'Cartera',   path: '/portfolio' },
  { icon: 'chart',     label: 'Sim',       path: '/simulation' },
  { icon: 'analytics', label: 'Analítica', path: '/analytics' },
  { icon: 'list',      label: 'Historial', path: '/history' },
  { icon: 'gear',      label: 'Config',    path: '/settings' },
] as const;

function NavIcon({ icon, color }: { icon: string; color: string }) {
  switch (icon) {
    case 'home':
      return <HomeIcon color={color} />;
    case 'portfolio':
      return <PortfolioIcon color={color} />;
    case 'chart':
      return <ChartIcon color={color} />;
    case 'list':
      return <ListIcon color={color} />;
    case 'analytics':
      return <AnalyticsIcon color={color} />;
    case 'gear':
      return <GearIcon color={color} />;
    default:
      return null;
  }
}

export function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: '50%',
        transform: 'translateX(-50%)',
        width: '100%',
        maxWidth: 430,
        background: 'var(--color-nav-bg)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        borderTop: '1px solid var(--color-glass-border)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        padding: '8px 0 20px',
        zIndex: 100,
      }}
    >
      {NAV_ITEMS.map((item) => {
        const isActive = item.path === '/'
          ? location.pathname === '/'
          : location.pathname.startsWith(item.path);
        const color = isActive
          ? 'var(--color-accent)'
          : 'var(--color-text-tertiary)';

        return (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
              }}
            >
              <NavIcon icon={item.icon} color={color} />
            </span>
            <span
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.08em',
                color,
                fontWeight: isActive ? 600 : 400,
                transition: 'color 0.2s ease',
              }}
            >
              {item.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
