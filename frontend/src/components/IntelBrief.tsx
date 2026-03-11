import { useState, useEffect, useCallback } from 'react';
import api from '../api';

interface BriefingResponse {
  summary: string;
  threat_level: string;
  recommended_action: string;
  generated_at: string;
}

interface BriefingZone {
  zone_id: string;
  zone_name: string;
  scan_count: number;
  event_count: number;
}

const THREAT_BADGE: Record<string, string> = {
  LOW: 'bg-green-900/30 text-green-400 border-green-800/40',
  MEDIUM: 'bg-amber-900/30 text-amber-400 border-amber-800/40',
  HIGH: 'bg-red-900/30 text-red-400 border-red-800/40',
  CRITICAL: 'bg-purple-900/30 text-purple-400 border-purple-800/40',
  UNKNOWN: 'bg-gray-900/30 text-gray-400 border-gray-800/40',
};

const COOLDOWN_SECONDS = 15 * 60; // 15 minutes

export default function IntelBrief() {
  const [zones, setZones] = useState<BriefingZone[]>([]);
  const [selectedZoneId, setSelectedZoneId] = useState('');
  const [brief, setBrief] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cooldownEnd, setCooldownEnd] = useState<number>(0);
  const [cooldownLeft, setCooldownLeft] = useState(0);

  useEffect(() => {
    loadZones();
  }, []);

  // Cooldown timer
  useEffect(() => {
    if (cooldownEnd <= 0) return;
    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.ceil((cooldownEnd - Date.now()) / 1000));
      setCooldownLeft(remaining);
      if (remaining <= 0) {
        setCooldownEnd(0);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldownEnd]);

  const loadZones = async () => {
    try {
      const resp = await api.get('/intel/briefing/zones');
      setZones(resp.data);
    } catch {
      // Silently fail — zones list is optional
    }
  };

  const generateBrief = useCallback(async () => {
    if (!selectedZoneId || loading) return;
    setLoading(true);
    setError('');
    setBrief(null);
    try {
      const resp = await api.post('/intel/briefing', {
        zone_id: selectedZoneId,
        hours_back: 4,
      });
      setBrief(resp.data);
      setCooldownEnd(Date.now() + COOLDOWN_SECONDS * 1000);
      setCooldownLeft(COOLDOWN_SECONDS);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Failed to generate briefing');
    } finally {
      setLoading(false);
    }
  }, [selectedZoneId, loading]);

  const formatCooldown = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const isOnCooldown = cooldownLeft > 0;

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-3">
      <h4 className="text-sm font-semibold text-[var(--color-text-dim)] uppercase tracking-wider">
        LLM Intel Brief
      </h4>

      {/* Zone selector + Generate button */}
      <div className="flex flex-col sm:flex-row gap-2">
        <select
          value={selectedZoneId}
          onChange={(e) => setSelectedZoneId(e.target.value)}
          className="flex-1 px-2 py-1.5 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-xs cursor-pointer"
        >
          <option value="">Select zone for briefing...</option>
          {zones.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>
              {z.zone_name} ({z.scan_count} scans, {z.event_count} events)
            </option>
          ))}
        </select>
        <button
          onClick={generateBrief}
          disabled={!selectedZoneId || loading || isOnCooldown}
          className="px-4 py-1.5 rounded bg-[var(--color-primary)] text-black text-xs font-medium hover:bg-[var(--color-primary-dim)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        >
          {loading ? (
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border border-black border-t-transparent rounded-full animate-spin" />
              Generating...
            </span>
          ) : isOnCooldown ? (
            `Cooldown ${formatCooldown(cooldownLeft)}`
          ) : (
            'Generate Intel Brief'
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="text-xs text-[var(--color-danger)] bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
          {error}
        </div>
      )}

      {/* Brief display */}
      {brief && (
        <div className="space-y-2">
          {/* Threat level badge */}
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded border ${THREAT_BADGE[brief.threat_level] || THREAT_BADGE.UNKNOWN}`}
            >
              {brief.threat_level}
            </span>
            <span className="text-xs text-[var(--color-text-dim)]">
              {brief.recommended_action}
            </span>
            <span className="text-[10px] text-[var(--color-text-dim)] ml-auto">
              {new Date(brief.generated_at).toLocaleTimeString()}
            </span>
          </div>

          {/* Summary text */}
          <div className="text-xs text-[var(--color-text)] leading-relaxed whitespace-pre-wrap bg-[var(--color-bg)] border border-[var(--color-border)] rounded p-3">
            {brief.summary}
          </div>
        </div>
      )}

      {/* No zones message */}
      {zones.length === 0 && !brief && (
        <div className="text-xs text-[var(--color-text-dim)] text-center py-2">
          No zones with recent activity. Add zones and submit scans to enable intel briefings.
        </div>
      )}
    </div>
  );
}
