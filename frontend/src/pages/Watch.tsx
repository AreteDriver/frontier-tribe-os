import { useEffect, useState } from 'react';
import api from '../api';

interface OrbitalZone {
  id: string;
  zone_id: string;
  name: string;
  feral_ai_tier: number;
  threat_level: string;
  last_scanned: string | null;
  scan_stale: boolean;
}

interface ScanResult {
  id: string;
  zone_id: string;
  scanner_id: string | null;
  result_type: string;
  signature_type: string | null;
  resolution: number;
  resolution_label: string;
  confidence: number;
  environment: string | null;
  scanned_at: string;
}

interface CloneQueue {
  total_active: number;
  total_manufacturing: number;
  low_reserve: boolean;
  reserve_threshold: number;
}

interface CrownRoster {
  total_members: number;
  members_with_crowns: number;
  members_without_crowns: number;
  crown_type_distribution: Record<string, number>;
}

interface BlindSpot {
  zone_id: string;
  name: string;
  unseen_minutes: number;
}

const THREAT_COLORS: Record<string, string> = {
  DORMANT: 'text-green-400 bg-green-900/20 border-green-800/30',
  ACTIVE: 'text-amber-400 bg-amber-900/20 border-amber-800/30',
  EVOLVED: 'text-red-400 bg-red-900/20 border-red-800/30',
  CRITICAL: 'text-purple-400 bg-purple-900/20 border-purple-800/30',
};

const SCAN_COLORS: Record<string, string> = {
  CLEAR: 'text-green-400 bg-green-900/30',
  ANOMALY: 'text-amber-400 bg-amber-900/30',
  HOSTILE: 'text-red-400 bg-red-900/30',
  UNKNOWN: 'text-gray-400 bg-gray-900/30',
};

const SIG_COLORS: Record<string, string> = {
  EM: 'text-cyan-400',
  HEAT: 'text-orange-400',
  GRAVIMETRIC: 'text-indigo-400',
  RADAR: 'text-emerald-400',
  UNKNOWN: 'text-gray-500',
};

const RESOLUTION_COLORS: Record<string, string> = {
  UNRESOLVED: 'bg-gray-600',
  PARTIAL: 'bg-amber-500',
  IDENTIFIED: 'bg-blue-500',
  FULL_INTEL: 'bg-green-500',
};

const TIER_BARS = [
  'bg-green-500',
  'bg-amber-500',
  'bg-orange-500',
  'bg-red-500',
  'bg-purple-500',
];

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

export default function Watch() {
  const [zones, setZones] = useState<OrbitalZone[]>([]);
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [clones, setClones] = useState<CloneQueue | null>(null);
  const [crowns, setCrowns] = useState<CrownRoster | null>(null);
  const [blindSpots, setBlindSpots] = useState<BlindSpot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Scan submission
  const [scanZoneId, setScanZoneId] = useState('');
  const [scanType, setScanType] = useState('CLEAR');
  const [scanSigType, setScanSigType] = useState('');
  const [scanResolution, setScanResolution] = useState(0);
  const [scanConf, setScanConf] = useState(100);

  // Zone creation
  const [newZoneName, setNewZoneName] = useState('');
  const [newZoneId, setNewZoneId] = useState('');

  const tribeId = localStorage.getItem('tribeId');

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setError('');
    try {
      const [zonesRes, scansRes, blindRes, clonesRes, crownsRes] = await Promise.all([
        api.get('/watch/orbital-zones'),
        api.get('/watch/scans/feed?limit=20'),
        api.get('/watch/alerts/blind-spots'),
        tribeId ? api.get('/watch/clones').catch(() => null) : null,
        tribeId ? api.get('/watch/crowns/roster').catch(() => null) : null,
      ]);
      setZones(zonesRes.data);
      setScans(scansRes.data);
      setBlindSpots(blindRes.data.blind_spots || []);
      if (clonesRes) setClones(clonesRes.data);
      if (crownsRes) setCrowns(crownsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load watch data');
    } finally {
      setLoading(false);
    }
  };

  const createZone = async () => {
    if (!newZoneName.trim() || !newZoneId.trim()) return;
    setError('');
    try {
      await api.post('/watch/orbital-zones', {
        zone_id: newZoneId.trim(),
        name: newZoneName.trim(),
      });
      setNewZoneName('');
      setNewZoneId('');
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create zone');
    }
  };

  const submitScan = async () => {
    if (!scanZoneId) return;
    setError('');
    try {
      await api.post('/watch/scans', {
        zone_id: scanZoneId,
        result_type: scanType,
        signature_type: scanSigType || null,
        resolution: scanResolution,
        confidence: scanConf,
      });
      loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit scan');
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold">Watch — C5 Intel</h2>
        <div className="flex items-center gap-3 py-8">
          <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-[var(--color-text-dim)]">Loading intel...</span>
        </div>
      </div>
    );
  }

  const criticalZones = zones.filter((z) => z.threat_level === 'CRITICAL').length;
  const staleZones = zones.filter((z) => z.scan_stale).length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h2 className="text-xl sm:text-2xl font-bold">Watch — C5 Intel</h2>
        <div className="flex gap-3 text-xs">
          <span className="text-[var(--color-text-dim)]">{zones.length} zones</span>
          {criticalZones > 0 && <span className="text-purple-400">{criticalZones} CRITICAL</span>}
          {staleZones > 0 && <span className="text-yellow-400">{staleZones} stale</span>}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {/* Top row: Stats + Clone + Crown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)]">{zones.length}</div>
          <div className="text-xs text-[var(--color-text-dim)]">Tracked Zones</div>
        </div>
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-[var(--color-primary)]">{scans.length}</div>
          <div className="text-xs text-[var(--color-text-dim)]">Recent Scans</div>
        </div>
        {clones && (
          <div className={`bg-[var(--color-surface)] border rounded-lg p-4 text-center ${clones.low_reserve ? 'border-red-800/50' : 'border-[var(--color-border)]'}`}>
            <div className={`text-2xl font-bold ${clones.low_reserve ? 'text-red-400' : 'text-[var(--color-primary)]'}`}>
              {clones.total_active}
            </div>
            <div className="text-xs text-[var(--color-text-dim)]">Active Clones</div>
            {clones.low_reserve && <div className="text-[10px] text-red-400 mt-1">LOW RESERVE</div>}
          </div>
        )}
        {crowns && (
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-[var(--color-primary)]">
              {crowns.members_with_crowns}/{crowns.total_members}
            </div>
            <div className="text-xs text-[var(--color-text-dim)]">Crowned</div>
          </div>
        )}
      </div>

      {/* Blind Spots Alert */}
      {blindSpots.length > 0 && (
        <div className="bg-yellow-900/10 border border-yellow-800/30 rounded-lg p-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
          <span className="text-yellow-400 text-sm font-semibold shrink-0">BLIND SPOTS</span>
          <div className="flex gap-2 flex-wrap">
            {blindSpots.slice(0, 5).map((bs) => (
              <span key={bs.zone_id} className="text-xs bg-yellow-900/30 text-yellow-400 px-2 py-0.5 rounded">
                {bs.name} ({bs.unseen_minutes}m)
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Orbital Zones */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] uppercase tracking-wider">Orbital Zones</h3>

          {zones.length === 0 ? (
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-8 text-center">
              <p className="text-[var(--color-text-dim)] text-sm mb-4">No zones tracked yet. Add your first zone.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {zones.map((z) => (
                <div
                  key={z.id}
                  className={`bg-[var(--color-surface)] border rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${THREAT_COLORS[z.threat_level]?.split(' ').pop() || 'border-[var(--color-border)]'}`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {/* Tier bars */}
                    <div className="flex gap-0.5 items-end h-5 shrink-0">
                      {[0, 1, 2, 3, 4].map((t) => (
                        <div
                          key={t}
                          className={`w-1 rounded-sm ${t <= z.feral_ai_tier ? TIER_BARS[t] : 'bg-gray-700'}`}
                          style={{ height: `${8 + t * 3}px` }}
                        />
                      ))}
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-sm truncate">{z.name}</div>
                      <div className="text-xs text-[var(--color-text-dim)] truncate">{z.zone_id}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                    {z.scan_stale && (
                      <span className="text-[10px] text-yellow-400 bg-yellow-900/30 px-1.5 py-0.5 rounded">STALE</span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded border ${THREAT_COLORS[z.threat_level] || ''}`}>
                      {z.threat_level}
                    </span>
                    <span className="text-xs text-[var(--color-text-dim)]">
                      {z.last_scanned ? timeAgo(z.last_scanned) : 'never'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Add Zone Form */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 sm:p-4">
            <div className="text-xs text-[var(--color-text-dim)] mb-2">Add Zone</div>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                placeholder="Zone ID (e.g. zone-alpha-7)"
                value={newZoneId}
                onChange={(e) => setNewZoneId(e.target.value)}
                className="flex-1 px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <input
                type="text"
                placeholder="Display name"
                value={newZoneName}
                onChange={(e) => setNewZoneName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && createZone()}
                className="flex-1 px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-sm placeholder-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={createZone}
                className="px-4 py-2 rounded bg-[var(--color-primary)] text-black text-sm font-medium hover:bg-[var(--color-primary-dim)] transition-colors cursor-pointer sm:w-auto w-full"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        {/* Right: Scan Feed */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-[var(--color-text-dim)] uppercase tracking-wider">Void Scan Feed</h3>

          {/* Submit Scan */}
          {zones.length > 0 && (
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 space-y-2">
              <select
                value={scanZoneId}
                onChange={(e) => setScanZoneId(e.target.value)}
                className="w-full px-2 py-1.5 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-xs cursor-pointer"
              >
                <option value="">Select zone...</option>
                {zones.map((z) => (
                  <option key={z.id} value={z.id}>{z.name}</option>
                ))}
              </select>
              <div className="flex gap-2">
                <select
                  value={scanType}
                  onChange={(e) => setScanType(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-xs cursor-pointer"
                >
                  <option value="CLEAR">CLEAR</option>
                  <option value="ANOMALY">ANOMALY</option>
                  <option value="HOSTILE">HOSTILE</option>
                  <option value="UNKNOWN">UNKNOWN</option>
                </select>
                <select
                  value={scanSigType}
                  onChange={(e) => setScanSigType(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-xs cursor-pointer"
                >
                  <option value="">Sig type...</option>
                  <option value="EM">EM</option>
                  <option value="HEAT">HEAT</option>
                  <option value="GRAVIMETRIC">GRAV</option>
                  <option value="RADAR">RADAR</option>
                  <option value="UNKNOWN">???</option>
                </select>
              </div>
              <div className="flex gap-2 items-center">
                <div className="flex-1">
                  <div className="flex justify-between text-[10px] text-[var(--color-text-dim)] mb-0.5">
                    <span>Resolution</span>
                    <span>{scanResolution}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={5}
                    value={scanResolution}
                    onChange={(e) => setScanResolution(parseInt(e.target.value))}
                    className="w-full h-1.5 rounded-full appearance-none bg-gray-700 cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--color-primary)]"
                  />
                </div>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={scanConf}
                  onChange={(e) => setScanConf(parseInt(e.target.value) || 0)}
                  className="w-14 px-2 py-1.5 rounded bg-[var(--color-bg)] border border-[var(--color-border)] text-[var(--color-text)] text-xs"
                  title="Confidence %"
                />
                <button
                  onClick={submitScan}
                  disabled={!scanZoneId}
                  className="px-3 py-1.5 rounded bg-[var(--color-primary)] text-black text-xs font-medium hover:bg-[var(--color-primary-dim)] cursor-pointer disabled:opacity-50"
                >
                  Scan
                </button>
              </div>
            </div>
          )}

          {/* Scan Results */}
          <div className="space-y-1.5 max-h-[500px] overflow-y-auto">
            {scans.length === 0 ? (
              <p className="text-sm text-[var(--color-text-dim)] text-center py-4">No scans yet</p>
            ) : (
              scans.map((s) => {
                const zone = zones.find((z) => z.id === s.zone_id);
                return (
                  <div
                    key={s.id}
                    className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-2 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${SCAN_COLORS[s.result_type] || ''}`}>
                          {s.result_type}
                        </span>
                        {s.signature_type && (
                          <span className={`text-[10px] font-mono ${SIG_COLORS[s.signature_type] || 'text-gray-500'}`}>
                            {s.signature_type}
                          </span>
                        )}
                        <span className="text-xs">{zone?.name || s.zone_id.slice(0, 8)}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-dim)]">
                        <span>{s.confidence}%</span>
                        <span>{timeAgo(s.scanned_at)}</span>
                      </div>
                    </div>
                    {/* Resolution bar */}
                    {s.resolution > 0 && (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 rounded-full bg-gray-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${RESOLUTION_COLORS[s.resolution_label] || 'bg-gray-600'}`}
                            style={{ width: `${s.resolution}%` }}
                          />
                        </div>
                        <span className="text-[9px] text-[var(--color-text-dim)] font-mono w-16 text-right">
                          {s.resolution_label?.replace('_', ' ')}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* HOSTILE warning */}
          {scans.some((s) => s.result_type === 'HOSTILE' && (Date.now() - new Date(s.scanned_at).getTime()) < 30 * 60000) && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg p-3 text-center">
              <div className="text-red-400 text-sm font-bold">SCAN BEFORE YOU MOVE</div>
              <div className="text-[10px] text-red-400/70">Hostile detected in last 30 min</div>
            </div>
          )}

          {/* Crown Distribution */}
          {crowns && Object.keys(crowns.crown_type_distribution).length > 0 && (
            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3">
              <h4 className="text-xs text-[var(--color-text-dim)] mb-2">Crown Types</h4>
              <div className="space-y-1">
                {Object.entries(crowns.crown_type_distribution).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-xs">
                    <span>{type}</span>
                    <span className="text-[var(--color-primary)]">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
