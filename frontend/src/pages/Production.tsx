import { useEffect, useState } from 'react';
import api from '../api';

interface Job {
  id: string;
  blueprint_name: string | null;
  quantity: number;
  status: string;
  materials_ready: boolean;
  assigned_to: string | null;
  assigned_name: string | null;
  created_at: string;
}

const STATUS_COLUMNS = ['queued', 'in_progress', 'blocked', 'complete'] as const;
const STATUS_COLORS: Record<string, string> = {
  queued: 'border-[var(--color-text-dim)]',
  in_progress: 'border-blue-500',
  blocked: 'border-[var(--color-danger)]',
  complete: 'border-[var(--color-primary)]',
};

export default function Production() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [newJobName, setNewJobName] = useState('');
  const [newJobQty, setNewJobQty] = useState(1);
  const [loading, setLoading] = useState(true);
  const tribeId = localStorage.getItem('tribeId');

  useEffect(() => {
    if (!tribeId) return;
    loadJobs();
  }, [tribeId]);

  const loadJobs = async () => {
    try {
      const { data } = await api.get(`/forge/tribes/${tribeId}/jobs`);
      setJobs(data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const createJob = async () => {
    if (!newJobName.trim() || !tribeId) return;
    try {
      await api.post(`/forge/tribes/${tribeId}/jobs`, {
        blueprint_name: newJobName,
        quantity: newJobQty,
      });
      setNewJobName('');
      setNewJobQty(1);
      loadJobs();
    } catch {
      // handled by interceptor
    }
  };

  const updateStatus = async (jobId: string, status: string) => {
    try {
      await api.patch(`/forge/tribes/${tribeId}/jobs/${jobId}`, { status });
      loadJobs();
    } catch {
      // handled by interceptor
    }
  };

  if (!tribeId) {
    return <p className="text-[var(--color-text-dim)]">No tribe selected.</p>;
  }

  const jobsByStatus = (status: string) => jobs.filter((j) => j.status === status);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Forge — Production Board</h2>
      </div>

      {/* Create job form */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-[var(--color-text-dim)] mb-1">Blueprint</label>
            <input
              type="text"
              placeholder="e.g. Fighter Ship"
              value={newJobName}
              onChange={(e) => setNewJobName(e.target.value)}
              className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
            />
          </div>
          <div className="w-24">
            <label className="block text-xs text-[var(--color-text-dim)] mb-1">Qty</label>
            <input
              type="number"
              min={1}
              value={newJobQty}
              onChange={(e) => setNewJobQty(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
            />
          </div>
          <button
            onClick={createJob}
            className="px-4 py-2 rounded bg-[var(--color-primary)] text-black font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer"
          >
            Add Job
          </button>
        </div>
      </div>

      {/* Kanban board */}
      <div className="grid grid-cols-4 gap-4">
        {STATUS_COLUMNS.map((status) => (
          <div key={status} className="space-y-3">
            <h3 className="text-sm font-semibold uppercase text-[var(--color-text-dim)] flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status === 'queued' ? 'bg-gray-500' : status === 'in_progress' ? 'bg-blue-500' : status === 'blocked' ? 'bg-red-500' : 'bg-[var(--color-primary)]'}`} />
              {status.replace('_', ' ')} ({jobsByStatus(status).length})
            </h3>
            <div className="space-y-2 min-h-[200px]">
              {jobsByStatus(status).map((job) => (
                <div
                  key={job.id}
                  className={`bg-[var(--color-surface)] border-l-2 ${STATUS_COLORS[job.status]} border border-[var(--color-border)] rounded-lg p-3 space-y-2`}
                >
                  <div className="font-medium text-sm">{job.blueprint_name}</div>
                  <div className="text-xs text-[var(--color-text-dim)]">
                    Qty: {job.quantity}
                    {job.assigned_name && ` • ${job.assigned_name}`}
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    {STATUS_COLUMNS.filter((s) => s !== status).map((s) => (
                      <button
                        key={s}
                        onClick={() => updateStatus(job.id, s)}
                        className="px-2 py-0.5 rounded text-xs border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer"
                      >
                        {s.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
