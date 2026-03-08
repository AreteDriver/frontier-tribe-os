import { NavLink, Outlet, useNavigate } from 'react-router-dom';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/roster', label: 'Census' },
  { to: '/production', label: 'Forge' },
  { to: '/treasury', label: 'Ledger' },
];

export default function Layout() {
  const navigate = useNavigate();
  const characterName = localStorage.getItem('characterName') || 'Pilot';

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('characterName');
    localStorage.removeItem('walletAddress');
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--color-border)] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <h1 className="text-lg font-bold text-[var(--color-primary)]">
            Tribe OS
          </h1>
          <nav className="flex gap-4">
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
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
