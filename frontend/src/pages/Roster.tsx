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

const ROLE_COLORS: Record<string, string> = {
  leader: 'text-yellow-400',
  officer: 'text-blue-400',
  member: 'text-[var(--color-primary)]',
  recruit: 'text-[var(--color-text-dim)]',
};

export default function Roster() {
  const [members, setMembers] = useState<Member[]>([]);
  const [requests, setRequests] = useState<JoinRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const tribeId = localStorage.getItem('tribeId');

  useEffect(() => {
    if (!tribeId) return;
    loadData();
  }, [tribeId]);

  const loadData = async () => {
    try {
      const [membersRes, requestsRes] = await Promise.all([
        api.get(`/census/tribes/${tribeId}/members`),
        api.get(`/census/tribes/${tribeId}/requests`).catch(() => ({ data: [] })),
      ]);
      setMembers(membersRes.data);
      setRequests(requestsRes.data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (requestId: string, action: 'approve' | 'deny') => {
    try {
      await api.post(`/census/tribes/${tribeId}/requests/${requestId}`, { action });
      loadData();
    } catch {
      // handled by interceptor
    }
  };

  const updateRole = async (memberId: string, role: string) => {
    try {
      await api.patch(`/census/tribes/${tribeId}/members/${memberId}/role`, { role });
      loadData();
    } catch {
      // handled by interceptor
    }
  };

  if (!tribeId) {
    return <p className="text-[var(--color-text-dim)]">No tribe selected. Create or join one from the Dashboard.</p>;
  }

  if (loading) {
    return <p className="text-[var(--color-text-dim)]">Loading roster...</p>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Census — Tribe Roster</h2>

      {requests.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-warning)] rounded-lg p-4 space-y-3">
          <h3 className="text-lg font-semibold text-[var(--color-warning)]">
            Pending Requests ({requests.length})
          </h3>
          {requests.map((req) => (
            <div key={req.id} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
              <span>{req.character_name || req.wallet_address}</span>
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

      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[var(--color-text-dim)]">
              <th className="text-left px-4 py-3">Character</th>
              <th className="text-left px-4 py-3">Role</th>
              <th className="text-left px-4 py-3">Timezone</th>
              <th className="text-left px-4 py-3">Joined</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-hover)]">
                <td className="px-4 py-3">{m.character_name || m.wallet_address}</td>
                <td className={`px-4 py-3 capitalize ${ROLE_COLORS[m.role] || ''}`}>{m.role}</td>
                <td className="px-4 py-3 text-[var(--color-text-dim)]">{m.timezone || '—'}</td>
                <td className="px-4 py-3 text-[var(--color-text-dim)]">
                  {new Date(m.joined_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  {m.role !== 'leader' && (
                    <select
                      value={m.role}
                      onChange={(e) => updateRole(m.id, e.target.value)}
                      className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-xs text-[var(--color-text)]"
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
