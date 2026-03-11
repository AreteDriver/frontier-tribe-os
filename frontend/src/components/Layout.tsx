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

      <header className="border-b border-[var(--color-border)] px-3 sm:px-6 py-3">
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-lg font-bold text-[var(--color-primary)] shrink-0">
            Tribe OS
          </h1>
          <div className="flex items-center gap-3 sm:gap-4">
            <span className="text-sm text-[var(--color-text-dim)] hidden sm:inline">{characterName}</span>
            <button
              onClick={logout}
              className="text-sm text-[var(--color-danger)] hover:underline cursor-pointer shrink-0"
            >
              Logout
            </button>
          </div>
        </div>
        <nav className="flex gap-1 sm:gap-3 mt-2 overflow-x-auto -mx-3 px-3 sm:mx-0 sm:px-0">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `px-2.5 sm:px-3 py-1 rounded text-sm whitespace-nowrap transition-colors ${
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
      </header>
      <main className="flex-1 p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
