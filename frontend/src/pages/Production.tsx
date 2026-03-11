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

interface Blueprint {
  type_id: string;
  name: string;
  category: string;
  materials: { item_id: string; name: string; quantity: number }[];
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

const STATUS_COLUMNS = ['queued', 'in_progress', 'blocked', 'complete'] as const;
const STATUS_COLORS: Record<string, string> = {
  queued: 'border-gray-500',
  in_progress: 'border-blue-500',
  blocked: 'border-[var(--color-danger)]',
  complete: 'border-[var(--color-primary)]',
};
const STATUS_DOTS: Record<string, string> = {
  queued: 'bg-gray-500',
  in_progress: 'bg-blue-500',
  blocked: 'bg-red-500',
  complete: 'bg-[var(--color-primary)]',
};

export default function Production() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [selectedBp, setSelectedBp] = useState('');
  const [newJobName, setNewJobName] = useState('');
  const [newJobQty, setNewJobQty] = useState(1);
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const tribeId = localStorage.getItem('tribeId');

  useEffect(() => {
    if (!tribeId) return;
    loadAll();
  }, [tribeId]);

  const loadAll = async () => {
    try {
      const [jobsRes, bpRes, gapRes] = await Promise.all([
        api.get(`/forge/tribes/${tribeId}/jobs`),
        api.get('/forge/blueprints').catch(() => ({ data: [] })),
        api.get(`/forge/tribes/${tribeId}/gap-analysis`).catch(() => ({ data: null })),
      ]);
      setJobs(jobsRes.data);
      setBlueprints(bpRes.data);
      if (gapRes.data) setGapAnalysis(gapRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const createJob = async () => {
    const bpName = selectedBp || newJobName.trim();
    if (!bpName || !tribeId) return;
    if (bpName.length > 200) {
      setError('Blueprint name too long (max 200 characters)');
      return;
    }
    if (newJobQty < 1 || newJobQty > 10000 || !Number.isInteger(newJobQty)) {
      setError('Quantity must be a whole number between 1 and 10,000');
      return;
    }
    setError('');
    try {
      await api.post(`/forge/tribes/${tribeId}/jobs`, {
        blueprint_name: bpName,
        quantity: newJobQty,
      });
      setSelectedBp('');
      setNewJobName('');
      setNewJobQty(1);
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create job');
    }
  };

  const updateStatus = async (jobId: string, status: string) => {
    setError('');
    try {
      await api.patch(`/forge/tribes/${tribeId}/jobs/${jobId}`, { status });
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const deleteJob = async (jobId: string) => {
    setError('');
    try {
      await api.delete(`/forge/tribes/${tribeId}/jobs/${jobId}`);
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete job');
    }
  };

  if (!tribeId) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Forge — Production Board</h2>
        <p className="text-[var(--color-text-dim)]">No tribe selected.</p>
      </div>
    );
  }

  const jobsByStatus = (status: string) => jobs.filter((j) => j.status === status);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Forge — Production Board</h2>
        <span className="text-sm text-[var(--color-text-dim)]">{jobs.length} job{jobs.length !== 1 ? 's' : ''}</span>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {/* Gap Analysis Panel */}
      {gapAnalysis && gapAnalysis.material_gaps.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-amber-800/30 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-amber-400">Material Gaps</h3>
            <div className="flex gap-3 text-xs text-[var(--color-text-dim)]">
              <span>{gapAnalysis.total_jobs} active jobs</span>
              <span>{gapAnalysis.jobs_materials_ready} ready</span>
              <span className="text-red-400">{gapAnalysis.jobs_blocked} blocked</span>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {gapAnalysis.material_gaps.map((gap) => (
              <div key={gap.item_id} className="flex items-center justify-between bg-[var(--color-bg)] rounded px-3 py-2">
                <span className="text-sm">{gap.item_name}</span>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[var(--color-text-dim)]">{gap.held}/{gap.required}</span>
                  <span className="text-red-400 font-medium">-{gap.deficit}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create job form */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="flex-1">
            <label className="block text-xs text-[var(--color-text-dim)] mb-1">Blueprint</label>
            {blueprints.length > 0 ? (
              <select
                value={selectedBp}
                onChange={(e) => { setSelectedBp(e.target.value); setNewJobName(''); }}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] cursor-pointer"
              >
                <option value="">Select blueprint...</option>
                {blueprints.map((bp) => (
                  <option key={bp.type_id} value={bp.type_id}>{bp.name} ({bp.category})</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="e.g. Fighter Ship"
                value={newJobName}
                onChange={(e) => setNewJobName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && createJob()}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
            )}
          </div>
          {blueprints.length > 0 && (
            <div className="flex-1">
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Or custom name</label>
              <input
                type="text"
                placeholder="Custom blueprint..."
                value={newJobName}
                onChange={(e) => { setNewJobName(e.target.value); setSelectedBp(''); }}
                onKeyDown={(e) => e.key === 'Enter' && createJob()}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
            </div>
          )}
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
      {loading ? (
        <div className="flex items-center gap-3 py-8 justify-center">
          <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-[var(--color-text-dim)]">Loading jobs...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {STATUS_COLUMNS.map((status) => (
            <div key={status} className="space-y-3">
              <h3 className="text-sm font-semibold uppercase text-[var(--color-text-dim)] flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${STATUS_DOTS[status]}`} />
                {status.replace('_', ' ')} ({jobsByStatus(status).length})
              </h3>
              <div className="space-y-2 min-h-[200px]">
                {jobsByStatus(status).map((job) => (
                  <div
                    key={job.id}
                    className={`bg-[var(--color-surface)] border-l-2 ${STATUS_COLORS[job.status]} border border-[var(--color-border)] rounded-lg p-3 space-y-2`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="font-medium text-sm">{job.blueprint_name}</div>
                      <button
                        onClick={() => deleteJob(job.id)}
                        className="text-xs text-[var(--color-text-dim)] hover:text-[var(--color-danger)] cursor-pointer ml-2"
                        title="Delete job"
                      >
                        &#10005;
                      </button>
                    </div>
                    <div className="text-xs text-[var(--color-text-dim)] flex items-center gap-2">
                      <span>Qty: {job.quantity}</span>
                      {job.materials_ready && (
                        <span className="text-green-400" title="Materials ready">&#10003; mats</span>
                      )}
                    </div>
                    {job.assigned_name && (
                      <div className="text-xs text-[var(--color-text-dim)]">
                        Assigned: <span className="text-[var(--color-text)]">{job.assigned_name}</span>
                      </div>
                    )}
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
      )}
    </div>
  );
}
