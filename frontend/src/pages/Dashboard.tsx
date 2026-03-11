import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

interface Tribe {
  id: string;
  name: string;
  name_short: string | null;
  invite_code: string | null;
  member_count: number;
  created_at: string;
}

interface MaterialGap {
  item_id: string;
  item_name: string;
  required: number;
  held: number;
  deficit: number;
}

interface GapAnalysis {
  total_jobs: number;
  jobs_materials_ready: number;
  jobs_blocked: number;
  material_gaps: MaterialGap[];
}

interface TreasurySummary {
  tribe_name: string;
  treasury_address: string | null;
  treasury_balances: { coin_type: string; total_balance: string; coin_object_count: number }[];
  member_count: number;
  total_transactions: number;
}

interface BlindSpotData {
  count: number;
  blind_spots: { zone_id: string; name: string; unseen_minutes: number }[];
}

function formatSui(mist: string): string {
  const n = BigInt(mist);
  const whole = n / BigInt(1_000_000_000);
  const frac = n % BigInt(1_000_000_000);
  if (frac === BigInt(0)) return whole.toString();
  return `${whole}.${frac.toString().padStart(9, '0').replace(/0+$/, '')}`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [tribe, setTribe] = useState<Tribe | null>(null);
  const [tribeName, setTribeName] = useState('');
  const [tribeShort, setTribeShort] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);
  const [treasury, setTreasury] = useState<TreasurySummary | null>(null);
  const [blindSpots, setBlindSpots] = useState<BlindSpotData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState('');
  const [error, setError] = useState('');
  const [joinSuccess, setJoinSuccess] = useState('');
  const characterName = localStorage.getItem('characterName') || 'Pilot';

  useEffect(() => {
    loadTribe();
  }, []);

  const loadTribe = async () => {
    const tribeId = localStorage.getItem('tribeId');
    if (!tribeId) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get(`/census/tribes/${tribeId}`);
      setTribe(data);

      // Load summary data in parallel
      const [gapRes, treasuryRes, blindRes] = await Promise.all([
        api.get(`/forge/tribes/${tribeId}/gap-analysis`).catch(() => null),
        api.get(`/ledger/tribes/${tribeId}/summary`).catch(() => null),
        api.get('/watch/alerts/blind-spots').catch(() => null),
      ]);
      if (gapRes) setGapAnalysis(gapRes.data);
      if (treasuryRes) setTreasury(treasuryRes.data);
      if (blindRes) setBlindSpots(blindRes.data);
    } catch {
      localStorage.removeItem('tribeId');
    } finally {
      setLoading(false);
    }
  };

  const createTribe = async () => {
    const trimmedName = tribeName.trim();
    if (!trimmedName) return;
    if (trimmedName.length > 100) {
      setError('Tribe name too long (max 100 characters)');
      return;
    }
    if (!/^[a-zA-Z0-9\s\-']+$/.test(trimmedName)) {
      setError('Tribe name contains invalid characters');
      return;
    }
    if (tribeShort && !/^[A-Z0-9]{1,10}$/.test(tribeShort)) {
      setError('Tag must be 1-10 uppercase letters/numbers');
      return;
    }
    setActionLoading(true);
    setError('');
    try {
      const { data } = await api.post('/census/tribes', {
        name: tribeName,
        name_short: tribeShort || null,
      });
      setTribe(data);
      localStorage.setItem('tribeId', data.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create tribe');
    } finally {
      setActionLoading(false);
    }
  };

  const joinTribe = async () => {
    const trimmedCode = inviteCode.trim();
    if (!trimmedCode) return;
    if (trimmedCode.length > 100) {
      setError('Invite code too long');
      return;
    }
    setActionLoading(true);
    setError('');
    setJoinSuccess('');
    try {
      const { data } = await api.post(`/census/tribes/join/${inviteCode}`);
      setJoinSuccess(`Join request submitted to ${data.tribe_name || 'tribe'}. Waiting for leader approval.`);
      setInviteCode('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join tribe');
    } finally {
      setActionLoading(false);
    }
  };

  const copyInviteCode = () => {
    if (tribe?.invite_code) {
      navigator.clipboard.writeText(tribe.invite_code);
    }
  };

  const syncWorldApi = async () => {
    if (!tribe) return;
    setSyncLoading(true);
    setSyncResult('');
    setError('');
    try {
      const { data } = await api.post(`/census/sync/tribes/${tribe.id}/members`);
      setSyncResult(`Synced: ${data.synced ?? 0} members updated from World API`);
      loadTribe();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'World API sync failed');
    } finally {
      setSyncLoading(false);
    }
  };

  const suiBalance = treasury?.treasury_balances.find((b) => b.coin_type.includes('::sui::SUI'));

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center py-12">
        <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Welcome, {characterName}</h2>

      {tribe ? (
        <div className="space-y-4">
          {/* Tribe Info Card */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 sm:p-6 space-y-4">
            <div className="flex items-center gap-3 flex-wrap">
              <h3 className="text-lg sm:text-xl font-semibold text-[var(--color-primary)]">{tribe.name}</h3>
              {tribe.name_short && (
                <span className="text-sm px-2 py-0.5 rounded bg-[var(--color-primary)]/10 text-[var(--color-primary)] border border-[var(--color-primary)]/20">
                  [{tribe.name_short}]
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-[var(--color-text-dim)]">Members</span>
                <p className="text-lg font-semibold">{tribe.member_count}</p>
              </div>
              <div className="min-w-0">
                <span className="text-[var(--color-text-dim)]">Invite Code</span>
                <p className="flex items-center gap-2">
                  <code className="bg-[var(--color-bg)] px-2 py-1 rounded text-[var(--color-primary)] text-sm truncate">
                    {tribe.invite_code}
                  </code>
                  <button
                    onClick={copyInviteCode}
                    className="text-xs text-[var(--color-text-dim)] hover:text-[var(--color-text)] cursor-pointer shrink-0"
                    title="Copy to clipboard"
                  >
                    copy
                  </button>
                </p>
              </div>
            </div>
            <button
              onClick={syncWorldApi}
              disabled={syncLoading}
              className="w-full py-2 rounded border border-[var(--color-border)] text-sm text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer disabled:opacity-50"
            >
              {syncLoading ? 'Syncing...' : 'Sync from World API'}
            </button>
          </div>

          {/* Summary Cards Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-[var(--color-primary)]">
                {gapAnalysis?.total_jobs ?? 0}
              </div>
              <div className="text-xs text-[var(--color-text-dim)]">Active Jobs</div>
            </div>
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div className={`text-2xl font-bold ${gapAnalysis?.jobs_blocked ? 'text-red-400' : 'text-[var(--color-primary)]'}`}>
                {gapAnalysis?.jobs_blocked ?? 0}
              </div>
              <div className="text-xs text-[var(--color-text-dim)]">Blocked</div>
            </div>
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-[var(--color-primary)]">
                {suiBalance ? formatSui(suiBalance.total_balance) : '0'}
              </div>
              <div className="text-xs text-[var(--color-text-dim)]">Treasury SUI</div>
            </div>
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-[var(--color-primary)]">
                {treasury?.total_transactions ?? 0}
              </div>
              <div className="text-xs text-[var(--color-text-dim)]">Transactions</div>
            </div>
          </div>

          {/* Material Gaps Alert */}
          {gapAnalysis && gapAnalysis.material_gaps.length > 0 && (
            <div className="bg-[var(--color-surface)] border border-amber-800/30 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-amber-400">Material Shortages</h3>
                <button
                  onClick={() => navigate('/production')}
                  className="text-xs text-[var(--color-text-dim)] hover:text-[var(--color-primary)] cursor-pointer"
                >
                  View in Forge &rarr;
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {gapAnalysis.material_gaps.slice(0, 6).map((gap) => (
                  <div key={gap.item_id} className="flex items-center justify-between bg-[var(--color-bg)] rounded px-3 py-1.5 text-xs min-w-0">
                    <span className="truncate mr-2">{gap.item_name}</span>
                    <span className="text-red-400 font-medium shrink-0">-{gap.deficit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Blind Spots Alert */}
          {blindSpots && blindSpots.count > 0 && (
            <div className="bg-[var(--color-surface)] border border-yellow-800/30 rounded-lg p-4 space-y-2">
              <h3 className="text-sm font-semibold text-yellow-400">
                Blind Spots ({blindSpots.count})
              </h3>
              <div className="space-y-1">
                {blindSpots.blind_spots.slice(0, 5).map((bs) => (
                  <div key={bs.zone_id} className="flex items-center justify-between text-xs">
                    <span>{bs.name}</span>
                    <span className="text-yellow-400">{bs.unseen_minutes}m unseen</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Module Nav Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <button
              onClick={() => navigate('/roster')}
              className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary)] transition-colors cursor-pointer text-center"
            >
              <div className="text-2xl mb-1">&#128101;</div>
              <div className="text-sm font-medium">Census</div>
              <div className="text-xs text-[var(--color-text-dim)]">Roster & roles</div>
            </button>
            <button
              onClick={() => navigate('/production')}
              className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary)] transition-colors cursor-pointer text-center"
            >
              <div className="text-2xl mb-1">&#9874;</div>
              <div className="text-sm font-medium">Forge</div>
              <div className="text-xs text-[var(--color-text-dim)]">Production board</div>
            </button>
            <button
              onClick={() => navigate('/treasury')}
              className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary)] transition-colors cursor-pointer text-center"
            >
              <div className="text-2xl mb-1">&#128176;</div>
              <div className="text-sm font-medium">Ledger</div>
              <div className="text-xs text-[var(--color-text-dim)]">Treasury & tokens</div>
            </button>
            <button
              onClick={() => navigate('/watch')}
              className="p-4 rounded-lg bg-[var(--color-surface)] border border-purple-800/30 hover:border-purple-500 transition-colors cursor-pointer text-center"
            >
              <div className="text-2xl mb-1">&#128065;</div>
              <div className="text-sm font-medium text-purple-400">Watch</div>
              <div className="text-xs text-[var(--color-text-dim)]">C5 intel & scans</div>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 sm:p-6 space-y-3">
            <h3 className="text-lg font-semibold">Create a Tribe</h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Tribe name"
                value={tribeName}
                onChange={(e) => setTribeName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && createTribe()}
                className="flex-1 px-4 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <input
                type="text"
                placeholder="Tag (e.g. WOLF)"
                maxLength={10}
                value={tribeShort}
                onChange={(e) => setTribeShort(e.target.value.toUpperCase())}
                className="sm:w-32 px-4 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={createTribe}
                disabled={actionLoading}
                className="px-4 py-2 rounded bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 sm:p-6 space-y-3">
            <h3 className="text-lg font-semibold">Join a Tribe</h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Paste invite code"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && joinTribe()}
                className="flex-1 px-4 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={joinTribe}
                disabled={actionLoading}
                className="px-4 py-2 rounded border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer disabled:opacity-50"
              >
                Join
              </button>
            </div>
          </div>
        </div>
      )}

      {(joinSuccess || syncResult) && (
        <div className="bg-green-900/20 border border-green-800/30 rounded-lg p-3 text-sm text-green-400">
          {joinSuccess || syncResult}
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}
    </div>
  );
}
