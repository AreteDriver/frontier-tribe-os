import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';

interface TopSystem {
  solar_system_id: number;
  count: number;
}

interface ActiveHour {
  hour: number;
  count: number;
}

interface RecentKill {
  kill_id: number;
  killer_address: string;
  killer_name: string | null;
  killer_corp_name: string | null;
  victim_address: string;
  victim_name: string | null;
  victim_corp_name: string | null;
  solar_system_id: number | null;
  timestamp: string;
  time_ago: string;
}

interface PilotProfile {
  address: string;
  name: string | null;
  kill_count: number;
  death_count: number;
  kd_ratio: number;
  primary_systems: TopSystem[];
  active_hours: ActiveHour[];
  recent_kills: RecentKill[];
  first_seen: string | null;
  last_seen: string | null;
  threat_level: string;
}

const threatColors: Record<string, string> = {
  LOW: 'bg-green-700 text-green-100',
  MEDIUM: 'bg-yellow-700 text-yellow-100',
  HIGH: 'bg-orange-700 text-orange-100',
  CRITICAL: 'bg-red-700 text-red-100',
};

export default function PilotProfilePage() {
  const { address } = useParams<{ address: string }>();
  const [profile, setProfile] = useState<PilotProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    api
      .get(`/intel/pilots/${address}`)
      .then((res) => setProfile(res.data))
      .catch((err) => {
        setError(err.response?.status === 404 ? 'Pilot not found' : 'Failed to load pilot data');
      })
      .finally(() => setLoading(false));
  }, [address]);

  if (loading) return <p className="text-[var(--color-text-dim)]">Loading...</p>;
  if (error) return <p className="text-[var(--color-danger)]">{error}</p>;
  if (!profile) return null;

  const maxHourCount = Math.max(...profile.active_hours.map((h) => h.count), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold text-[var(--color-primary)]">
          {profile.name || profile.address.slice(0, 12)}
        </h2>
        <span className={`px-2 py-0.5 rounded text-xs font-bold ${threatColors[profile.threat_level] || 'bg-gray-700'}`}>
          {profile.threat_level}
        </span>
      </div>
      <p className="text-xs text-[var(--color-text-dim)] font-mono">{profile.address}</p>

      {/* Stats cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[var(--color-surface)] rounded px-4 py-3">
          <div className="text-xs text-[var(--color-text-dim)]">Kills</div>
          <div className="text-xl font-bold text-red-400">{profile.kill_count}</div>
        </div>
        <div className="bg-[var(--color-surface)] rounded px-4 py-3">
          <div className="text-xs text-[var(--color-text-dim)]">Deaths</div>
          <div className="text-xl font-bold text-amber-400">{profile.death_count}</div>
        </div>
        <div className="bg-[var(--color-surface)] rounded px-4 py-3">
          <div className="text-xs text-[var(--color-text-dim)]">K/D Ratio</div>
          <div className="text-xl font-bold">{profile.kd_ratio}</div>
        </div>
        <div className="bg-[var(--color-surface)] rounded px-4 py-3">
          <div className="text-xs text-[var(--color-text-dim)]">Threat</div>
          <div className={`text-xl font-bold ${profile.threat_level === 'CRITICAL' ? 'text-red-400' : profile.threat_level === 'HIGH' ? 'text-orange-400' : profile.threat_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'}`}>
            {profile.threat_level}
          </div>
        </div>
      </div>

      {/* First/last seen */}
      <div className="flex gap-6 text-sm text-[var(--color-text-dim)]">
        {profile.first_seen && <span>First seen: {new Date(profile.first_seen).toLocaleDateString()}</span>}
        {profile.last_seen && <span>Last seen: {new Date(profile.last_seen).toLocaleDateString()}</span>}
      </div>

      {/* Active hours chart */}
      {profile.active_hours.length > 0 && (
        <div>
          <h3 className="text-sm font-bold mb-2">Active Hours (UTC)</h3>
          <div className="flex items-end gap-px h-24">
            {Array.from({ length: 24 }, (_, h) => {
              const entry = profile.active_hours.find((a) => a.hour === h);
              const count = entry?.count || 0;
              const pct = (count / maxHourCount) * 100;
              return (
                <div key={h} className="flex-1 flex flex-col items-center gap-0.5">
                  <div
                    className="w-full bg-[var(--color-primary)] rounded-t opacity-80"
                    style={{ height: `${Math.max(pct, 2)}%` }}
                    title={`${h}:00 — ${count} kills`}
                  />
                  {h % 6 === 0 && (
                    <span className="text-[8px] text-[var(--color-text-dim)]">{h}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top systems */}
      {profile.primary_systems.length > 0 && (
        <div>
          <h3 className="text-sm font-bold mb-2">Top Systems</h3>
          <div className="flex gap-3">
            {profile.primary_systems.map((s) => (
              <div key={s.solar_system_id} className="bg-[var(--color-surface)] rounded px-3 py-2 text-sm">
                <span className="text-[var(--color-text-dim)]">sys:</span>{s.solar_system_id}{' '}
                <span className="text-xs text-[var(--color-text-dim)]">({s.count})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent kills table */}
      <div>
        <h3 className="text-sm font-bold mb-2">Recent Kills</h3>
        <div className="space-y-1">
          {profile.recent_kills.map((k) => (
            <div key={k.kill_id} className="flex items-center justify-between text-sm px-3 py-1.5 bg-[var(--color-surface)] rounded">
              <div className="flex gap-3 items-center">
                <Link to={`/intel/pilots/${k.killer_address}`} className="text-red-400 hover:underline">
                  {k.killer_name || k.killer_address.slice(0, 10)}
                </Link>
                <span className="text-[var(--color-text-dim)]">killed</span>
                <Link to={`/intel/pilots/${k.victim_address}`} className="text-amber-300 hover:underline">
                  {k.victim_name || k.victim_address.slice(0, 10)}
                </Link>
              </div>
              <span className="text-xs text-[var(--color-text-dim)]">{k.time_ago}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
