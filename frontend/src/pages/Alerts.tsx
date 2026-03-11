import { useEffect, useState } from 'react';
import api from '../api';

interface AlertConfig {
  id: string;
  tribe_id: string;
  created_by: string;
  alert_type: string;
  target_id: string | null;
  target_name: string | null;
  threshold: number;
  discord_webhook_url: string;
  enabled: boolean;
  cooldown_minutes: number;
  last_triggered: string | null;
  created_at: string;
}

const ALERT_TYPES = [
  { value: 'kill_in_zone', label: 'Kill in Zone', color: 'text-red-400 bg-red-900/20' },
  { value: 'corp_spotted', label: 'Corp Spotted', color: 'text-amber-400 bg-amber-900/20' },
  { value: 'hostile_scan', label: 'Hostile Scan', color: 'text-orange-400 bg-orange-900/20' },
  { value: 'feral_evolved', label: 'Feral Evolved', color: 'text-purple-400 bg-purple-900/20' },
  { value: 'blind_spot', label: 'Blind Spot', color: 'text-yellow-400 bg-yellow-900/20' },
  { value: 'clone_low', label: 'Clone Low', color: 'text-cyan-400 bg-cyan-900/20' },
];

function getAlertTypeInfo(type: string) {
  return ALERT_TYPES.find((t) => t.value === type) || { value: type, label: type, color: 'text-gray-400 bg-gray-900/20' };
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [formType, setFormType] = useState('kill_in_zone');
  const [formTargetId, setFormTargetId] = useState('');
  const [formTargetName, setFormTargetName] = useState('');
  const [formThreshold, setFormThreshold] = useState(1);
  const [formWebhook, setFormWebhook] = useState('');
  const [formCooldown, setFormCooldown] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const loadAlerts = async () => {
    setError('');
    try {
      const res = await api.get('/alerts');
      setAlerts(res.data);
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      setError(msg || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const toggleAlert = async (alert: AlertConfig) => {
    try {
      await api.patch(`/alerts/${alert.id}`, { enabled: !alert.enabled });
      setAlerts((prev) =>
        prev.map((a) => (a.id === alert.id ? { ...a, enabled: !a.enabled } : a))
      );
    } catch {
      setToast('Failed to toggle alert');
    }
  };

  const deleteAlert = async (id: string) => {
    try {
      await api.delete(`/alerts/${id}`);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      setToast('Alert deleted');
    } catch {
      setToast('Failed to delete alert');
    }
  };

  const testAlert = async (id: string) => {
    try {
      const res = await api.post(`/alerts/${id}/test`);
      if (res.data.sent) {
        setToast('Test alert sent successfully');
      } else {
        setToast('Test alert failed to send');
      }
    } catch {
      setToast('Failed to send test alert');
    }
  };

  const createAlert = async () => {
    if (!formWebhook.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      await api.post('/alerts', {
        alert_type: formType,
        target_id: formTargetId.trim() || null,
        target_name: formTargetName.trim() || null,
        threshold: formThreshold,
        discord_webhook_url: formWebhook.trim(),
        cooldown_minutes: formCooldown,
      });
      setFormTargetId('');
      setFormTargetName('');
      setFormThreshold(1);
      setFormWebhook('');
      setFormCooldown(5);
      setShowForm(false);
      setToast('Alert created');
      loadAlerts();
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      setError(msg || 'Failed to create alert');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold">Alerts</h2>
        <div className="flex items-center gap-3 py-8">
          <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-[var(--color-text-dim)]">Loading alerts...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold">Alerts</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded bg-[var(--color-primary)] text-black text-sm font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer"
        >
          {showForm ? 'Cancel' : '+ New Alert'}
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-primary)] rounded-lg p-3 text-sm text-[var(--color-primary)]">
          {toast}
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {/* Create Alert Form */}
      {showForm && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] uppercase tracking-wider">
            New Alert Configuration
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Alert Type</label>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm cursor-pointer"
              >
                {ALERT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">
                Target {formType === 'kill_in_zone' || formType === 'blind_spot' ? '(Zone ID)' : formType === 'corp_spotted' ? '(Corp Name)' : '(ID)'}
              </label>
              <input
                type="text"
                placeholder={formType === 'corp_spotted' ? 'Corp name...' : 'zone-alpha-1'}
                value={formTargetId}
                onChange={(e) => setFormTargetId(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
            </div>

            <div>
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Display Name</label>
              <input
                type="text"
                placeholder="Alpha Sector"
                value={formTargetName}
                onChange={(e) => setFormTargetName(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
            </div>

            <div>
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Threshold</label>
              <input
                type="number"
                min={1}
                value={formThreshold}
                onChange={(e) => setFormThreshold(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm focus:outline-none focus:border-[var(--color-primary)]"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Discord Webhook URL</label>
              <input
                type="text"
                placeholder="https://discord.com/api/webhooks/..."
                value={formWebhook}
                onChange={(e) => setFormWebhook(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <p className="text-[10px] text-[var(--color-text-dim)] mt-1">
                Must start with https://discord.com/api/webhooks/ or https://discordapp.com/api/webhooks/
              </p>
            </div>

            <div>
              <label className="block text-xs text-[var(--color-text-dim)] mb-1">Cooldown (minutes)</label>
              <input
                type="number"
                min={1}
                value={formCooldown}
                onChange={(e) => setFormCooldown(parseInt(e.target.value) || 5)}
                className="w-full px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm focus:outline-none focus:border-[var(--color-primary)]"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={createAlert}
              disabled={submitting || !formWebhook.trim()}
              className="px-4 py-2 rounded bg-[var(--color-primary)] text-black text-sm font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </div>
      )}

      {/* Alert List */}
      {alerts.length === 0 ? (
        <div className="border border-dashed border-[var(--color-border)] rounded-lg p-8 text-center">
          <p className="text-sm text-[var(--color-text-dim)]">
            No alerts configured. Set up Discord notifications for threat events.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => {
            const info = getAlertTypeInfo(alert.alert_type);
            return (
              <div
                key={alert.id}
                className={`bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 sm:p-4 ${!alert.enabled ? 'opacity-50' : ''}`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono shrink-0 ${info.color}`}>
                      {info.label}
                    </span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">
                        {alert.target_name || alert.target_id || 'Any'}
                      </div>
                      <div className="text-xs text-[var(--color-text-dim)]">
                        Threshold: {alert.threshold} | Cooldown: {alert.cooldown_minutes}m
                        {alert.last_triggered && (
                          <> | Last: {timeAgo(alert.last_triggered)}</>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Toggle */}
                    <button
                      onClick={() => toggleAlert(alert)}
                      className={`relative w-10 h-5 rounded-full transition-colors cursor-pointer ${
                        alert.enabled ? 'bg-green-600' : 'bg-gray-600'
                      }`}
                      title={alert.enabled ? 'Disable' : 'Enable'}
                    >
                      <span
                        className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                          alert.enabled ? 'left-5' : 'left-0.5'
                        }`}
                      />
                    </button>

                    {/* Test */}
                    <button
                      onClick={() => testAlert(alert.id)}
                      className="px-2 py-1 rounded text-xs border border-[var(--color-border)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:border-[var(--color-primary)] transition-colors cursor-pointer"
                      title="Send test alert"
                    >
                      Test
                    </button>

                    {/* Delete */}
                    <button
                      onClick={() => deleteAlert(alert.id)}
                      className="px-2 py-1 rounded text-xs text-[var(--color-danger)] hover:bg-red-900/20 transition-colors cursor-pointer"
                      title="Delete alert"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
