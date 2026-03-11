import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api';

interface TopSystem {
  solar_system_id: number;
  count: number;
}

interface TopKiller {
  address: string;
  name: string | null;
  kill_count: number;
}

interface RecentKill {
  kill_id: number;
  killer_address: string;
  killer_name: string | null;
  victim_address: string;
  victim_name: string | null;
  solar_system_id: number | null;
  timestamp: string;
  time_ago: string;
}

interface CorpProfile {
  corp_id: number;
  corp_name: string | null;
  kill_count: number;
  death_count: number;
  efficiency: number;
  member_addresses: string[];
  primary_systems: TopSystem[];
  recent_kills: RecentKill[];
  top_killers: TopKiller[];
}

export default function CorpProfilePage() {
  const { corpId } = useParams<{ corpId: string }>();
  const [profile, setProfile] = useState<CorpProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!corpId) return;
    setLoading(true);
    api
      .get(`/intel/corps/${corpId}`)
      .then((res) => setProfile(res.data))
      .catch((err) => {
        setError(err.response?.status === 404 ? 'Corp not found' : 'Failed to load corp data');
      })
      .finally(() => setLoading(false));
  }, [corpId]);

  if (loading) return <p className="text-[var(--color-text-dim)]">Loading...</p>;
  if (error) return <p className="text-[var(--color-danger)]">{error}</p>;
  if (!profile) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-[var(--color-primary)]">
        {profile.corp_name || `Corp #${profile.corp_id}`}
      </h2>

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
          <div className="text-xs text-[var(--color-text-dim)]">Efficiency</div>
          <div className="text-xl font-bold text-green-400">{profile.efficiency}%</div>
        </div>
        <div className="bg-[var(--color-surface)] rounded px-4 py-3">
          <div className="text-xs text-[var(--color-text-dim)]">Members</div>
          <div className="text-xl font-bold">{profile.member_addresses.length}</div>
        </div>
      </div>

      {/* Top killers */}
      {profile.top_killers.length > 0 && (
        <div>
          <h3 className="text-sm font-bold mb-2">Top Killers</h3>
          <div className="space-y-1">
            {profile.top_killers.map((k) => (
              <div key={k.address} className="flex items-center justify-between text-sm px-3 py-1.5 bg-[var(--color-surface)] rounded">
                <Link to={`/intel/pilots/${k.address}`} className="text-red-400 hover:underline">
                  {k.name || k.address.slice(0, 10)}
                </Link>
                <span className="font-bold">{k.kill_count} kills</span>
              </div>
            ))}
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

      {/* Recent kills */}
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
