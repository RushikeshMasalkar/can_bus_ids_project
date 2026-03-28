import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Activity, BarChart3, FileCheck2, HelpCircle, Menu, ShieldCheck, X } from 'lucide-react';
import { apiClient, type HealthResponse } from '../api/client';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: Activity },
  { to: '/analyze', label: 'Analyze', icon: ShieldCheck },
  { to: '/reports', label: 'Reports', icon: FileCheck2 },
  { to: '/about', label: 'About', icon: HelpCircle },
];

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const location = useLocation();

  useEffect(() => {
    let active = true;
    apiClient
      .getHealth()
      .then((data) => {
        if (active) {
          setHealth(data);
        }
      })
      .catch(() => {
        if (active) {
          setHealth(null);
        }
      });
    return () => {
      active = false;
    };
  }, [location.pathname]);

  const pageLabel = useMemo(() => {
    const entry = NAV_ITEMS.find((item) => location.pathname.startsWith(item.to));
    return entry?.label ?? 'CAN-IDS';
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <Link to="/dashboard" className="brand-link" onClick={() => setMobileOpen(false)}>
            <div className="brand-badge">
              <BarChart3 size={18} />
            </div>
            <div>
              <div className="brand-title">CAN-IDS</div>
              <div className="brand-subtitle">Enterprise Console</div>
            </div>
          </Link>
          <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }: { isActive: boolean }) => `nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="status-pill">
            <span className={`status-dot ${health?.status === 'online' ? 'online' : 'offline'}`} />
            <span>{health?.status === 'online' ? 'System Online' : 'Backend Offline'}</span>
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <div>
            <h1 className="page-title">{pageLabel}</h1>
            <p className="page-subtitle">CAN Bus Intrusion Detection Platform</p>
          </div>
          <nav className="topbar-nav-links">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={`top-${item.to}`}
                to={item.to}
                className={({ isActive }: { isActive: boolean }) => `topbar-link ${isActive ? 'active' : ''}`}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="topbar-status">
            <span>Model: {health?.model ?? 'unknown'}</span>
            <span>Device: {health?.device ?? 'n/a'}</span>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
