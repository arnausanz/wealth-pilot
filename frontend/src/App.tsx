import { Routes, Route } from 'react-router-dom';
import { NavBar } from './components/ui/NavBar';
import { DashboardScreen } from './features/dashboard/DashboardScreen';
import { PortfolioScreen } from './features/portfolio/PortfolioScreen';
import { SimulationScreen } from './features/simulation/SimulationScreen';
import { HistoryScreen } from './features/history/HistoryScreen';
import { SettingsScreen } from './features/settings/SettingsScreen';
import { AnalyticsScreen } from './features/analytics/AnalyticsScreen';

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
          <Route path="/simulation" element={<SimulationScreen />} />
          <Route path="/history"    element={<HistoryScreen />} />
          <Route path="/settings"   element={<SettingsScreen />} />
          <Route path="/analytics"  element={<AnalyticsScreen />} />
        </Routes>
      </div>
      <NavBar />
    </>
  );
}
