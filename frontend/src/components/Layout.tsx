import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import api from '../api';

interface CycleInfo {
  cycle: number;
  cycle_name: string;
  days_elapsed: number;
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/roster', label: 'Census' },
  { to: '/production', label: 'Forge' },
  { to: '/treasury', label: 'Ledger' },
  { to: '/watch', label: 'Watch' },
];

export default function Layout() {
  const navigate = useNavigate();
  const characterName = localStorage.getItem('characterName') || 'Pilot';
  const [cycle, setCycle] = useState<CycleInfo | null>(null);

  useEffect(() => {
    api.get('/watch/cycle').then((res) => setCycle(res.data)).catch(() => {});
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('characterName');
    localStorage.removeItem('walletAddress');
    localStorage.removeItem('tribeId');
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Cycle Banner */}
      {cycle && (
        <div className="bg-purple-900/30 border-b border-purple-800/40 px-4 py-1.5 text-center text-xs font-mono tracking-widest text-purple-300">
          CYCLE {cycle.cycle} // {cycle.cycle_name.toUpperCase()} // DAY {cycle.days_elapsed}
        </div>
      )}

      <header className="border-b border-[var(--color-border)] px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-4 sm:gap-8">
          <h1 className="text-lg font-bold text-[var(--color-primary)]">
            Tribe OS
          </h1>
          <nav className="flex gap-2 sm:gap-4 flex-wrap">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `px-3 py-1 rounded text-sm transition-colors ${
                    isActive
                      ? 'bg-[var(--color-primary)] text-black font-medium'
                      : 'text-[var(--color-text-dim)] hover:text-[var(--color-text)]'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[var(--color-text-dim)]">{characterName}</span>
          <button
            onClick={logout}
            className="text-sm text-[var(--color-danger)] hover:underline cursor-pointer"
          >
            Logout
          </button>
        </div>
      </header>
      <main className="flex-1 p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
