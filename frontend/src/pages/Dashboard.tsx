import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

interface Tribe {
  id: string;
  name: string;
  invite_code: string | null;
  member_count: number;
  created_at: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [tribe, setTribe] = useState<Tribe | null>(null);
  const [tribeName, setTribeName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const characterName = localStorage.getItem('characterName') || 'Pilot';

  const createTribe = async () => {
    if (!tribeName.trim()) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/census/tribes', { name: tribeName });
      setTribe(data);
      localStorage.setItem('tribeId', data.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create tribe');
    } finally {
      setLoading(false);
    }
  };

  const joinTribe = async () => {
    if (!inviteCode.trim()) return;
    setLoading(true);
    setError('');
    try {
      await api.post(`/census/tribes/join/${inviteCode}`);
      setError(''); // Would redirect after approval
      alert('Join request submitted! Wait for leader approval.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join tribe');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Welcome, {characterName}</h2>

      {tribe ? (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-4">
          <h3 className="text-xl font-semibold text-[var(--color-primary)]">{tribe.name}</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-[var(--color-text-dim)]">Members:</span>{' '}
              {tribe.member_count}
            </div>
            <div>
              <span className="text-[var(--color-text-dim)]">Invite Code:</span>{' '}
              <code className="bg-[var(--color-bg)] px-2 py-1 rounded text-[var(--color-primary)]">
                {tribe.invite_code}
              </code>
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => navigate('/roster')}
              className="px-4 py-2 rounded bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer"
            >
              View Roster
            </button>
            <button
              onClick={() => navigate('/production')}
              className="px-4 py-2 rounded border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
            >
              Production Board
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-3">
            <h3 className="text-lg font-semibold">Create a Tribe</h3>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Tribe name"
                value={tribeName}
                onChange={(e) => setTribeName(e.target.value)}
                className="flex-1 px-4 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={createTribe}
                disabled={loading}
                className="px-4 py-2 rounded bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>

          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 space-y-3">
            <h3 className="text-lg font-semibold">Join a Tribe</h3>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Invite code"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                className="flex-1 px-4 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={joinTribe}
                disabled={loading}
                className="px-4 py-2 rounded border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer disabled:opacity-50"
              >
                Join
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-[var(--color-danger)]">{error}</p>
      )}
    </div>
  );
}
