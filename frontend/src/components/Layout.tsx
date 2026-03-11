import { useEffect, useState, useRef } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import api from '../api';

interface CycleInfo {
  cycle: number;
  cycle_name: string;
  days_elapsed: number;
}

interface SearchPilot {
  address: string;
  name: string | null;
}

interface SearchCorp {
  corp_id: number;
  corp_name: string | null;
}

interface SearchZone {
  zone_id: string;
  name: string;
  id: string;
}

interface SearchResults {
  pilots: SearchPilot[];
  corps: SearchCorp[];
  zones: SearchZone[];
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/roster', label: 'Census' },
  { to: '/production', label: 'Forge' },
  { to: '/treasury', label: 'Ledger' },
  { to: '/watch', label: 'Watch' },
  { to: '/intel', label: 'Intel' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/systems', label: 'Systems' },
];

export default function Layout() {
  const navigate = useNavigate();
  const characterName = localStorage.getItem('characterName') || 'Pilot';
  const [cycle, setCycle] = useState<CycleInfo | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [showResults, setShowResults] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get('/watch/cycle').then((res) => setCycle(res.data)).catch(() => {});
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (q: string) => {
    setSearchQuery(q);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (q.length < 2) {
      setSearchResults(null);
      setShowResults(false);
      return;
    }
    searchTimeout.current = setTimeout(async () => {
      try {
        const res = await api.get('/intel/search', { params: { q } });
        setSearchResults(res.data);
        setShowResults(true);
      } catch {
        setSearchResults(null);
      }
    }, 300);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowResults(false);
    }
  };

  const closeAndNavigate = (path: string) => {
    setShowResults(false);
    setSearchQuery('');
    navigate(path);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('characterName');
    localStorage.removeItem('walletAddress');
    localStorage.removeItem('tribeId');
    navigate('/');
  };

  const hasResults =
    searchResults &&
    (searchResults.pilots.length > 0 ||
      searchResults.corps.length > 0 ||
      searchResults.zones.length > 0);

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
            {/* Global Search */}
            <div className="relative" ref={searchRef}>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-dim)] text-xs pointer-events-none">
                  &#x1F50D;
                </span>
                <input
                  type="text"
                  placeholder="Search pilots, corps, zones..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => {
                    if (searchQuery.length >= 2 && searchResults) setShowResults(true);
                  }}
                  className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded pl-8 pr-3 py-1.5 text-sm w-48 sm:w-64 focus:outline-none focus:border-[var(--color-primary)] transition-colors"
                />
              </div>
              {showResults && hasResults && (
                <div className="absolute top-full right-0 mt-1 w-72 bg-[var(--color-surface)] border border-[var(--color-border)] rounded shadow-lg z-50 max-h-80 overflow-y-auto">
                  {searchResults.pilots.length > 0 && (
                    <div>
                      <div className="px-3 py-1.5 text-xs font-bold text-[var(--color-text-dim)] uppercase tracking-wider border-b border-[var(--color-border)]">
                        Pilots
                      </div>
                      {searchResults.pilots.map((p) => (
                        <button
                          key={p.address}
                          onClick={() => closeAndNavigate(`/intel/pilots/${p.address}`)}
                          className="block w-full text-left px-3 py-2 text-sm hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                        >
                          <span className="text-[var(--color-primary)]">{p.name || 'Unknown'}</span>
                          <span className="text-xs text-[var(--color-text-dim)] ml-2">
                            {p.address.slice(0, 10)}...
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                  {searchResults.corps.length > 0 && (
                    <div>
                      <div className="px-3 py-1.5 text-xs font-bold text-[var(--color-text-dim)] uppercase tracking-wider border-b border-[var(--color-border)]">
                        Corps
                      </div>
                      {searchResults.corps.map((c) => (
                        <button
                          key={c.corp_id}
                          onClick={() => closeAndNavigate(`/intel/corps/${c.corp_id}`)}
                          className="block w-full text-left px-3 py-2 text-sm hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                        >
                          <span className="text-amber-300">{c.corp_name || 'Unknown Corp'}</span>
                          <span className="text-xs text-[var(--color-text-dim)] ml-2">
                            ID: {c.corp_id}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                  {searchResults.zones.length > 0 && (
                    <div>
                      <div className="px-3 py-1.5 text-xs font-bold text-[var(--color-text-dim)] uppercase tracking-wider border-b border-[var(--color-border)]">
                        Zones
                      </div>
                      {searchResults.zones.map((z) => (
                        <button
                          key={z.id}
                          onClick={() => closeAndNavigate('/systems')}
                          className="block w-full text-left px-3 py-2 text-sm hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                        >
                          <span className="text-green-400">{z.name}</span>
                          <span className="text-xs text-[var(--color-text-dim)] ml-2">
                            {z.zone_id}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {showResults && searchResults && !hasResults && searchQuery.length >= 2 && (
                <div className="absolute top-full right-0 mt-1 w-72 bg-[var(--color-surface)] border border-[var(--color-border)] rounded shadow-lg z-50 px-3 py-3 text-sm text-[var(--color-text-dim)]">
                  No results found.
                </div>
              )}
            </div>
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
