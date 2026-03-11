import { useEffect, useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

interface Killmail {
  id: string;
  kill_id: number;
  victim_address: string;
  victim_name: string | null;
  victim_corp_name: string | null;
  killer_address: string;
  killer_name: string | null;
  killer_corp_name: string | null;
  solar_system_id: number | null;
  timestamp: string;
  time_ago: string;
  raw_json?: string;
}

interface KillmailStats {
  total_24h: number;
  total_7d: number;
  hourly_kills: { hour: string; count: number }[];
  top_systems: { solar_system_id: number; count: number }[];
}

interface PilotSearchResult {
  address: string;
  name: string | null;
}

function getRowTint(timestamp: string): string {
  const age = Date.now() - new Date(timestamp).getTime();
  const oneHour = 3600_000;
  const oneDay = 86400_000;
  if (age < oneHour) return 'border-l-4 border-red-500 bg-red-950/20';
  if (age < oneDay) return 'border-l-4 border-amber-500 bg-amber-950/10';
  return 'border-l-4 border-gray-700';
}

export default function KillFeed() {
  const [kills, setKills] = useState<Killmail[]>([]);
  const [stats, setStats] = useState<KillmailStats | null>(null);
  const [search, setSearch] = useState('');
  const [systemFilter, setSystemFilter] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [pilotQuery, setPilotQuery] = useState('');
  const [pilotResults, setPilotResults] = useState<PilotSearchResult[]>([]);
  const [showPilotResults, setShowPilotResults] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchKills = useCallback(async () => {
    try {
      const params: Record<string, string> = { limit: '100' };
      if (search) params.corp_name = search;
      if (systemFilter) params.system_id = systemFilter;
      const res = await api.get('/intel/killmails', { params });
      setKills(res.data);
    } catch {
      // silent — auth interceptor handles 401
    } finally {
      setLoading(false);
    }
  }, [search, systemFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/intel/killmails/stats');
      setStats(res.data);
    } catch {
      // silent
    }
  }, []);

  const handlePilotSearch = (q: string) => {
    setPilotQuery(q);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (q.length < 2) {
      setPilotResults([]);
      setShowPilotResults(false);
      return;
    }
    searchTimeout.current = setTimeout(async () => {
      try {
        const res = await api.get('/intel/pilots/search', { params: { q } });
        setPilotResults(res.data);
        setShowPilotResults(true);
      } catch {
        setPilotResults([]);
      }
    }, 300);
  };

  useEffect(() => {
    fetchKills();
    fetchStats();
    const interval = setInterval(() => {
      fetchKills();
      fetchStats();
    }, 30_000);
    return () => clearInterval(interval);
  }, [fetchKills, fetchStats]);

  const filteredKills = kills.filter((k) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      (k.victim_name?.toLowerCase().includes(s)) ||
      (k.killer_name?.toLowerCase().includes(s)) ||
      (k.victim_corp_name?.toLowerCase().includes(s)) ||
      (k.killer_corp_name?.toLowerCase().includes(s))
    );
  });

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-[var(--color-primary)]">Intel - Kill Feed</h2>

      {/* Stats banner */}
      {stats && (
        <div className="flex gap-4 text-sm">
          <div className="bg-[var(--color-surface)] rounded px-4 py-2">
            <span className="text-[var(--color-text-dim)]">24h Kills:</span>{' '}
            <span className="font-bold text-red-400">{stats.total_24h}</span>
          </div>
          <div className="bg-[var(--color-surface)] rounded px-4 py-2">
            <span className="text-[var(--color-text-dim)]">7d Kills:</span>{' '}
            <span className="font-bold text-amber-400">{stats.total_7d}</span>
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Filter name / corp..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1.5 text-sm flex-1 max-w-xs"
        />
        <input
          type="text"
          placeholder="System ID"
          value={systemFilter}
          onChange={(e) => setSystemFilter(e.target.value)}
          className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1.5 text-sm w-32"
        />
        <div className="relative">
          <input
            type="text"
            placeholder="Search pilot..."
            value={pilotQuery}
            onChange={(e) => handlePilotSearch(e.target.value)}
            onBlur={() => setTimeout(() => setShowPilotResults(false), 200)}
            className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1.5 text-sm w-48"
          />
          {showPilotResults && pilotResults.length > 0 && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-[var(--color-surface)] border border-[var(--color-border)] rounded shadow-lg z-10 max-h-48 overflow-y-auto">
              {pilotResults.map((p) => (
                <Link
                  key={p.address}
                  to={`/intel/pilots/${p.address}`}
                  className="block px-3 py-2 text-sm hover:bg-[var(--color-border)] transition-colors"
                >
                  <span className="text-[var(--color-primary)]">{p.name || 'Unknown'}</span>
                  <span className="text-xs text-[var(--color-text-dim)] ml-2">{p.address.slice(0, 10)}...</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Kill list */}
      {loading ? (
        <p className="text-[var(--color-text-dim)]">Loading...</p>
      ) : filteredKills.length === 0 ? (
        <p className="text-[var(--color-text-dim)]">No killmails found.</p>
      ) : (
        <div className="space-y-1">
          {filteredKills.map((k) => (
            <div key={k.kill_id}>
              <button
                onClick={() => setExpandedId(expandedId === k.kill_id ? null : k.kill_id)}
                className={`w-full text-left px-3 py-2 rounded transition-all cursor-pointer ${getRowTint(k.timestamp)} hover:bg-[var(--color-surface)]`}
              >
                <div className="flex items-center justify-between text-sm">
                  <div className="flex gap-4 items-center">
                    <Link to={`/intel/pilots/${k.killer_address}`} className="text-red-400 font-medium hover:underline" onClick={(e) => e.stopPropagation()}>
                      {k.killer_name || k.killer_address.slice(0, 10)}
                    </Link>
                    <span className="text-[var(--color-text-dim)]">killed</span>
                    <Link to={`/intel/pilots/${k.victim_address}`} className="text-amber-300 hover:underline" onClick={(e) => e.stopPropagation()}>
                      {k.victim_name || k.victim_address.slice(0, 10)}
                    </Link>
                    {k.solar_system_id && (
                      <span className="text-[var(--color-text-dim)] text-xs">
                        sys:{k.solar_system_id}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-[var(--color-text-dim)] shrink-0 ml-2">
                    {k.time_ago}
                  </span>
                </div>
              </button>

              {expandedId === k.kill_id && (
                <div className="ml-4 mt-1 mb-2 p-3 bg-[var(--color-surface)] rounded text-xs space-y-1 border border-[var(--color-border)]">
                  <div><span className="text-[var(--color-text-dim)]">Kill ID:</span> {k.kill_id}</div>
                  <div><span className="text-[var(--color-text-dim)]">Killer:</span> {k.killer_name} ({k.killer_address})</div>
                  {k.killer_corp_name && (
                    <div><span className="text-[var(--color-text-dim)]">Killer Corp:</span> {k.killer_corp_name}</div>
                  )}
                  <div><span className="text-[var(--color-text-dim)]">Victim:</span> {k.victim_name} ({k.victim_address})</div>
                  {k.victim_corp_name && (
                    <div><span className="text-[var(--color-text-dim)]">Victim Corp:</span> {k.victim_corp_name}</div>
                  )}
                  <div><span className="text-[var(--color-text-dim)]">System:</span> {k.solar_system_id ?? 'Unknown'}</div>
                  <div><span className="text-[var(--color-text-dim)]">Time:</span> {new Date(k.timestamp).toLocaleString()}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
