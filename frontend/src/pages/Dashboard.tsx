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

export default function Dashboard() {
  const navigate = useNavigate();
  const [tribe, setTribe] = useState<Tribe | null>(null);
  const [tribeName, setTribeName] = useState('');
  const [tribeShort, setTribeShort] = useState('');
  const [inviteCode, setInviteCode] = useState('');
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
    } catch {
      // Tribe may have been deleted — clear stale reference
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

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center py-12">
        <div className="w-6 h-6 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Welcome, {characterName}</h2>

      {tribe ? (
        <div className="space-y-4">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-4">
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-semibold text-[var(--color-primary)]">{tribe.name}</h3>
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
              <div>
                <span className="text-[var(--color-text-dim)]">Invite Code</span>
                <p className="flex items-center gap-2">
                  <code className="bg-[var(--color-bg)] px-2 py-1 rounded text-[var(--color-primary)] text-sm">
                    {tribe.invite_code}
                  </code>
                  <button
                    onClick={copyInviteCode}
                    className="text-xs text-[var(--color-text-dim)] hover:text-[var(--color-text)] cursor-pointer"
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

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-3">
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

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-3">
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
