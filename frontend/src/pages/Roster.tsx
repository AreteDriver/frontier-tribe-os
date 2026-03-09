import { useEffect, useState } from 'react';
import api from '../api';

interface Member {
  id: string;
  wallet_address: string;
  character_name: string | null;
  role: string;
  timezone: string | null;
  last_active: string | null;
  joined_at: string;
}

interface JoinRequest {
  id: string;
  wallet_address: string;
  character_name: string | null;
  status: string;
  requested_at: string;
}

const ROLE_BADGES: Record<string, string> = {
  leader: 'bg-yellow-900/30 text-yellow-400 border-yellow-800/30',
  officer: 'bg-blue-900/30 text-blue-400 border-blue-800/30',
  member: 'bg-green-900/30 text-green-400 border-green-800/30',
  recruit: 'bg-gray-900/30 text-gray-400 border-gray-800/30',
};

export default function Roster() {
  const [members, setMembers] = useState<Member[]>([]);
  const [requests, setRequests] = useState<JoinRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const tribeId = localStorage.getItem('tribeId');

  useEffect(() => {
    if (!tribeId) return;
    loadData();
  }, [tribeId]);

  const loadData = async () => {
    setError('');
    try {
      const [membersRes, requestsRes] = await Promise.all([
        api.get(`/census/tribes/${tribeId}/members`),
        api.get(`/census/tribes/${tribeId}/requests`).catch(() => ({ data: [] })),
      ]);
      setMembers(membersRes.data);
      setRequests(requestsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load roster');
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (requestId: string, action: 'approve' | 'deny') => {
    try {
      await api.post(`/census/tribes/${tribeId}/requests/${requestId}`, { action });
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${action} request`);
    }
  };

  const updateRole = async (memberId: string, role: string) => {
    try {
      await api.patch(`/census/tribes/${tribeId}/members/${memberId}/role`, { role });
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update role');
    }
  };

  if (!tribeId) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold">Census — Tribe Roster</h2>
        <p className="text-[var(--color-text-dim)]">No tribe selected. Create or join one from the Dashboard.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold">Census — Tribe Roster</h2>
        <div className="flex items-center gap-3 py-8">
          <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-[var(--color-text-dim)]">Loading roster...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Census — Tribe Roster</h2>
        <span className="text-sm text-[var(--color-text-dim)]">{members.length} member{members.length !== 1 ? 's' : ''}</span>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {requests.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-warning)]/50 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-[var(--color-warning)]">
            Pending Requests ({requests.length})
          </h3>
          {requests.map((req) => (
            <div key={req.id} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
              <div>
                <span className="font-medium">{req.character_name || 'Unknown'}</span>
                <span className="text-xs text-[var(--color-text-dim)] ml-2 font-mono">
                  {req.wallet_address.slice(0, 10)}...
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleRequest(req.id, 'approve')}
                  className="px-3 py-1 rounded text-sm bg-[var(--color-primary)] text-black hover:bg-[var(--color-primary-dim)] cursor-pointer"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleRequest(req.id, 'deny')}
                  className="px-3 py-1 rounded text-sm border border-[var(--color-danger)] text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white cursor-pointer"
                >
                  Deny
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-x-auto">
        <table className="w-full text-sm min-w-[600px]">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[var(--color-text-dim)]">
              <th className="text-left px-4 py-3">Character</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-left px-4 py-3">Wallet</th>
              <th className="text-left px-4 py-3">Joined</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-hover)]">
                <td className="px-4 py-3 font-medium">{m.character_name || 'Unknown'}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded border ${ROLE_BADGES[m.role] || ''}`}>
                    {m.role}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-[var(--color-text-dim)]">
                  {m.wallet_address.slice(0, 8)}...{m.wallet_address.slice(-4)}
                </td>
                <td className="px-4 py-3 text-[var(--color-text-dim)]">
                  {new Date(m.joined_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  {m.role !== 'leader' && (
                    <select
                      value={m.role}
                      onChange={(e) => updateRole(m.id, e.target.value)}
                      className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs text-[var(--color-text)] cursor-pointer"
                    >
                      <option value="recruit">Recruit</option>
                      <option value="member">Member</option>
                      <option value="officer">Officer</option>
                    </select>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {members.length === 0 && (
          <p className="px-4 py-8 text-center text-[var(--color-text-dim)]">No members yet</p>
        )}
      </div>
    </div>
  );
}
