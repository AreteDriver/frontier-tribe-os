import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

interface BattleSide {
  corp_name: string | null;
  corp_id: number | null;
  kill_count: number;
  death_count: number;
  addresses: string[];
  efficiency: number;
}

interface BattleSummary {
  battle_id: string;
  solar_system_id: number;
  start_time: string;
  end_time: string;
  total_kills: number;
  sides: BattleSide[];
  preview: string[];
}

interface TimelineEntry {
  kill_id: number;
  killer_name: string | null;
  killer_address: string;
  killer_corp_name: string | null;
  victim_name: string | null;
  victim_address: string;
  victim_corp_name: string | null;
  timestamp: string;
}

interface BattleDetail {
  battle_id: string;
  solar_system_id: number;
  start_time: string;
  end_time: string;
  total_kills: number;
  duration_minutes: number;
  sides: BattleSide[];
  timeline: TimelineEntry[];
  narrative: string | null;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

function formatDuration(minutes: number): string {
  if (minutes < 1) return '<1 min';
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m`;
}

function EfficiencyBar({ efficiency }: { efficiency: number }) {
  const width = Math.max(0, Math.min(100, efficiency));
  const color = efficiency >= 70 ? 'bg-green-500' : efficiency >= 40 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="w-20 bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${width}%` }} />
      </div>
      <span className="text-[var(--color-text-dim)]">{efficiency.toFixed(1)}%</span>
    </div>
  );
}

function SideCard({ side }: { side: BattleSide }) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-bold text-[var(--color-primary)]">
          {side.corp_id ? (
            <Link to={`/intel/corps/${side.corp_id}`} className="hover:underline">
              {side.corp_name || `Corp #${side.corp_id}`}
            </Link>
          ) : (
            side.corp_name || 'Unknown'
          )}
        </h4>
        <span className="text-xs text-[var(--color-text-dim)]">{side.addresses.length} pilots</span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
        <div>
          <span className="text-[var(--color-text-dim)]">Kills:</span>{' '}
          <span className="text-green-400 font-medium">{side.kill_count}</span>
        </div>
        <div>
          <span className="text-[var(--color-text-dim)]">Deaths:</span>{' '}
          <span className="text-red-400 font-medium">{side.death_count}</span>
        </div>
      </div>
      <EfficiencyBar efficiency={side.efficiency} />
    </div>
  );
}

function BattleDetailView({ battle, onBack }: { battle: BattleDetail; onBack: () => void }) {
  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="text-sm text-[var(--color-primary)] hover:underline cursor-pointer"
      >
        &larr; Back to battles
      </button>

      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-[var(--color-primary)]">
          Battle in System {battle.solar_system_id}
        </h3>
        <span className="text-sm text-[var(--color-text-dim)]">
          {formatDuration(battle.duration_minutes)} &middot; {battle.total_kills} kills
        </span>
      </div>

      <div className="text-xs text-[var(--color-text-dim)]">
        {formatTime(battle.start_time)} &mdash; {formatTime(battle.end_time)}
      </div>

      {/* Narrative */}
      {battle.narrative && (
        <div className="bg-purple-900/20 border border-purple-800/40 rounded p-4">
          <h4 className="text-sm font-bold text-purple-300 mb-2">Intel Narrative</h4>
          <p className="text-sm text-[var(--color-text)] whitespace-pre-wrap">{battle.narrative}</p>
        </div>
      )}

      {/* Sides */}
      <div>
        <h4 className="text-sm font-bold text-[var(--color-text-dim)] mb-2">Combatants</h4>
        <div className={`grid gap-3 ${battle.sides.length === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
          {battle.sides.map((side, i) => (
            <SideCard key={i} side={side} />
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div>
        <h4 className="text-sm font-bold text-[var(--color-text-dim)] mb-2">Timeline</h4>
        <div className="space-y-1">
          {battle.timeline.map((entry) => (
            <div
              key={entry.kill_id}
              className="flex items-center gap-3 text-sm py-1.5 px-3 bg-[var(--color-surface)] rounded border-l-2 border-red-500/50"
            >
              <span className="text-xs text-[var(--color-text-dim)] shrink-0 w-20 font-mono">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
              <div className="flex items-center gap-2 flex-wrap">
                <Link
                  to={`/intel/pilots/${entry.killer_address}`}
                  className="text-red-400 font-medium hover:underline"
                >
                  {entry.killer_name || entry.killer_address.slice(0, 10)}
                </Link>
                {entry.killer_corp_name && (
                  <span className="text-xs text-[var(--color-text-dim)]">[{entry.killer_corp_name}]</span>
                )}
                <span className="text-[var(--color-text-dim)]">killed</span>
                <Link
                  to={`/intel/pilots/${entry.victim_address}`}
                  className="text-amber-300 hover:underline"
                >
                  {entry.victim_name || entry.victim_address.slice(0, 10)}
                </Link>
                {entry.victim_corp_name && (
                  <span className="text-xs text-[var(--color-text-dim)]">[{entry.victim_corp_name}]</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function BattleReport() {
  const [battles, setBattles] = useState<BattleSummary[]>([]);
  const [selectedBattle, setSelectedBattle] = useState<BattleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    const fetchBattles = async () => {
      try {
        const res = await api.get('/intel/battles');
        setBattles(res.data);
      } catch {
        // silent — auth interceptor handles 401
      } finally {
        setLoading(false);
      }
    };
    fetchBattles();
  }, []);

  const loadDetail = async (battleId: string) => {
    setDetailLoading(true);
    try {
      const res = await api.get(`/intel/battles/${battleId}`);
      setSelectedBattle(res.data);
    } catch {
      // silent
    } finally {
      setDetailLoading(false);
    }
  };

  if (selectedBattle) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-[var(--color-primary)]">Battle Report</h2>
        <BattleDetailView battle={selectedBattle} onBack={() => setSelectedBattle(null)} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-[var(--color-primary)]">Battle Reports</h2>
      <p className="text-sm text-[var(--color-text-dim)]">
        Detected engagements: 3+ kills in the same system within a 30-minute window.
      </p>

      {loading ? (
        <p className="text-[var(--color-text-dim)]">Scanning killmails...</p>
      ) : battles.length === 0 ? (
        <p className="text-[var(--color-text-dim)]">No battles detected.</p>
      ) : (
        <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
          {battles.map((b) => (
            <button
              key={b.battle_id}
              onClick={() => loadDetail(b.battle_id)}
              disabled={detailLoading}
              className="text-left bg-[var(--color-surface)] border border-[var(--color-border)] rounded p-4 hover:border-[var(--color-primary)] transition-colors cursor-pointer disabled:opacity-50"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-[var(--color-primary)]">
                  System {b.solar_system_id}
                </span>
                <span className="text-sm font-bold text-red-400">{b.total_kills} kills</span>
              </div>
              <div className="text-xs text-[var(--color-text-dim)] mb-2">
                {formatTime(b.start_time)} &mdash; {formatTime(b.end_time)}
              </div>
              <div className="flex flex-wrap gap-2 mb-2">
                {b.sides.map((side, i) => (
                  <span
                    key={i}
                    className="text-xs bg-[var(--color-border)] rounded px-2 py-0.5"
                  >
                    {side.corp_name || 'Unknown'}: {side.kill_count}K / {side.death_count}D
                  </span>
                ))}
              </div>
              <div className="text-xs text-[var(--color-text-dim)] space-y-0.5">
                {b.preview.map((p, i) => (
                  <div key={i}>{p}</div>
                ))}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
