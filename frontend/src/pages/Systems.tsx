import { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import api from '../api';

interface HotspotEntry {
  zone_id: string;
  name: string;
  scan_count_24h: number;
  threat_level: string;
  feral_ai_tier: number;
  last_scanned: string | null;
  trend: string;
  predicted_scans_1h: number;
  predicted_scans_2h: number;
}

interface HourlyScan {
  hour: string;
  count: number;
}

interface ThreatHistoryEntry {
  timestamp: string;
  tier: number;
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

interface ActiveScanner {
  scanner_id: string;
  scan_count: number;
}

interface ZoneActivity {
  zone_id: string;
  name: string;
  hourly_scans: HourlyScan[];
  threat_history: ThreatHistoryEntry[];
  recent_scans: ScanResult[];
  active_scanners: ActiveScanner[];
}

const THREAT_COLORS: Record<string, string> = {
  DORMANT: 'text-green-400',
  ACTIVE: 'text-amber-400',
  EVOLVED: 'text-red-400',
  CRITICAL: 'text-purple-400',
};

const SCAN_COLORS: Record<string, string> = {
  CLEAR: 'text-green-400 bg-green-900/30',
  ANOMALY: 'text-amber-400 bg-amber-900/30',
  HOSTILE: 'text-red-400 bg-red-900/30',
  UNKNOWN: 'text-gray-400 bg-gray-900/30',
};

const RESOLUTION_COLORS: Record<string, string> = {
  UNRESOLVED: 'bg-gray-600',
  PARTIAL: 'bg-amber-500',
  IDENTIFIED: 'bg-blue-500',
  FULL_INTEL: 'bg-green-500',
};

type DetailTab = 'activity' | 'threats' | 'scans' | 'scanners';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

function TrendIndicator({ trend }: { trend: string }) {
  if (trend === 'UP') return <span className="text-green-400 font-bold">&#9650;</span>;
  if (trend === 'DOWN') return <span className="text-red-400 font-bold">&#9660;</span>;
  return <span className="text-gray-500 font-bold">&#9654;</span>;
}

type SortKey = 'name' | 'scan_count_24h' | 'threat_level' | 'trend' | 'last_scanned';

export default function Systems() {
  const [hotspots, setHotspots] = useState<HotspotEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [zoneActivity, setZoneActivity] = useState<ZoneActivity | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<DetailTab>('activity');
  const [sortKey, setSortKey] = useState<SortKey>('scan_count_24h');
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    loadHotspots();
  }, []);

  const loadHotspots = async () => {
    setError('');
    try {
      const res = await api.get('/watch/systems/hotspots');
      setHotspots(res.data.hotspots || []);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to load hotspots');
    } finally {
      setLoading(false);
    }
  };

  const loadZoneActivity = async (zoneId: string) => {
    setActivityLoading(true);
    setActiveTab('activity');
    try {
      const res = await api.get(`/watch/systems/${zoneId}/activity`);
      setZoneActivity(res.data);
      setSelectedZone(zoneId);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to load zone activity');
    } finally {
      setActivityLoading(false);
    }
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const sortedHotspots = [...hotspots].sort((a, b) => {
    const dir = sortAsc ? 1 : -1;
    switch (sortKey) {
      case 'name':
        return dir * a.name.localeCompare(b.name);
      case 'scan_count_24h':
        return dir * (a.scan_count_24h - b.scan_count_24h);
      case 'threat_level':
        return dir * a.threat_level.localeCompare(b.threat_level);
      case 'trend': {
        const order: Record<string, number> = { UP: 3, FLAT: 2, DOWN: 1 };
        return dir * ((order[a.trend] || 0) - (order[b.trend] || 0));
      }
      case 'last_scanned': {
        const aTime = a.last_scanned ? new Date(a.last_scanned).getTime() : 0;
        const bTime = b.last_scanned ? new Date(b.last_scanned).getTime() : 0;
        return dir * (aTime - bTime);
      }
      default:
        return 0;
    }
  });

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className="px-3 py-2 text-left text-xs font-medium text-[var(--color-text-dim)] uppercase tracking-wider cursor-pointer hover:text-[var(--color-text)] select-none"
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? '\u25B2' : '\u25BC') : ''}
    </th>
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold">Systems Intelligence</h2>
        <div className="flex items-center gap-3 py-8">
          <div className="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
          <span className="text-[var(--color-text-dim)]">Loading system data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold">Systems Intelligence</h2>
        <span className="text-xs text-[var(--color-text-dim)]">{hotspots.length} zones tracked</span>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {/* Hotspot Table */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[var(--color-bg)]">
              <tr>
                <SortHeader label="Zone Name" field="name" />
                <SortHeader label="24h Scans" field="scan_count_24h" />
                <SortHeader label="Threat Level" field="threat_level" />
                <SortHeader label="Trend" field="trend" />
                <th className="px-3 py-2 text-left text-xs font-medium text-[var(--color-text-dim)] uppercase tracking-wider" title="Predicted (7-day hourly average)">+1h</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-[var(--color-text-dim)] uppercase tracking-wider" title="Predicted (7-day hourly average)">+2h</th>
                <SortHeader label="Last Scanned" field="last_scanned" />
              </tr>
            </thead>
            <tbody>
              {sortedHotspots.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-sm text-[var(--color-text-dim)]">
                    No zones with activity data. Add zones in Watch first.
                  </td>
                </tr>
              ) : (
                sortedHotspots.map((h) => (
                  <tr
                    key={h.zone_id}
                    className={`border-t border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-bg)] transition-colors ${
                      selectedZone === h.zone_id ? 'bg-[var(--color-bg)]' : ''
                    }`}
                    onClick={() => loadZoneActivity(h.zone_id)}
                  >
                    <td className="px-3 py-2.5 text-sm font-medium">{h.name}</td>
                    <td className="px-3 py-2.5 text-sm text-[var(--color-primary)] font-mono">
                      {h.scan_count_24h}
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`text-xs font-medium ${THREAT_COLORS[h.threat_level] || 'text-gray-400'}`}>
                        {h.threat_level}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <TrendIndicator trend={h.trend} />
                    </td>
                    <td className="px-3 py-2.5 text-sm text-zinc-500 font-mono" title="Predicted (7-day hourly average)">
                      {h.predicted_scans_1h}
                    </td>
                    <td className="px-3 py-2.5 text-sm text-zinc-500 font-mono" title="Predicted (7-day hourly average)">
                      {h.predicted_scans_2h}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-[var(--color-text-dim)]">
                      {h.last_scanned ? timeAgo(h.last_scanned) : 'never'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Zone Detail Panel */}
      {selectedZone && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
          {activityLoading ? (
            <div className="p-6 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-[var(--color-text-dim)]">Loading zone detail...</span>
            </div>
          ) : zoneActivity ? (
            <div>
              {/* Zone header */}
              <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
                <h3 className="text-lg font-semibold">{zoneActivity.name}</h3>
                <button
                  onClick={() => { setSelectedZone(null); setZoneActivity(null); }}
                  className="text-xs text-[var(--color-text-dim)] hover:text-[var(--color-text)] cursor-pointer"
                >
                  Close
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-[var(--color-border)]">
                {(
                  [
                    { key: 'activity', label: 'Activity' },
                    { key: 'threats', label: 'Threat History' },
                    { key: 'scans', label: 'Recent Scans' },
                    { key: 'scanners', label: 'Active Scanners' },
                  ] as { key: DetailTab; label: string }[]
                ).map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`px-4 py-2 text-sm cursor-pointer transition-colors ${
                      activeTab === tab.key
                        ? 'text-[var(--color-primary)] border-b-2 border-[var(--color-primary)]'
                        : 'text-[var(--color-text-dim)] hover:text-[var(--color-text)]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              <div className="p-4">
                {activeTab === 'activity' && (
                  <div>
                    <h4 className="text-xs text-[var(--color-text-dim)] uppercase tracking-wider mb-3">
                      Hourly Scan Count (24h)
                    </h4>
                    {zoneActivity.hourly_scans.length > 0 ? (
                      <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={zoneActivity.hourly_scans}>
                          <defs>
                            <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <XAxis
                            dataKey="hour"
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                            allowDecimals={false}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1f2937',
                              border: '1px solid #374151',
                              borderRadius: '6px',
                              fontSize: '12px',
                            }}
                            labelStyle={{ color: '#9ca3af' }}
                          />
                          <Area
                            type="monotone"
                            dataKey="count"
                            stroke="#10b981"
                            fill="url(#scanGradient)"
                            strokeWidth={2}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-[var(--color-text-dim)] py-4 text-center">No scan data available.</p>
                    )}
                  </div>
                )}

                {activeTab === 'threats' && (
                  <div>
                    <h4 className="text-xs text-[var(--color-text-dim)] uppercase tracking-wider mb-3">
                      Feral AI Tier Over Time
                    </h4>
                    {zoneActivity.threat_history.length > 0 ? (
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={zoneActivity.threat_history}>
                          <XAxis
                            dataKey="timestamp"
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                            tickFormatter={(v: string) => {
                              const d = new Date(v);
                              return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
                            }}
                          />
                          <YAxis
                            domain={[0, 4]}
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                            allowDecimals={false}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1f2937',
                              border: '1px solid #374151',
                              borderRadius: '6px',
                              fontSize: '12px',
                            }}
                            labelStyle={{ color: '#9ca3af' }}
                          />
                          <Line
                            type="stepAfter"
                            dataKey="tier"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            dot={{ fill: '#f59e0b', r: 3 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-[var(--color-text-dim)] py-4 text-center">No threat history recorded.</p>
                    )}
                  </div>
                )}

                {activeTab === 'scans' && (
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    <h4 className="text-xs text-[var(--color-text-dim)] uppercase tracking-wider mb-3">
                      Last 20 Scans
                    </h4>
                    {zoneActivity.recent_scans.length === 0 ? (
                      <p className="text-sm text-[var(--color-text-dim)] py-4 text-center">No scans recorded.</p>
                    ) : (
                      zoneActivity.recent_scans.map((s) => (
                        <div
                          key={s.id}
                          className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-3 py-2 space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${SCAN_COLORS[s.result_type] || ''}`}>
                                {s.result_type}
                              </span>
                              {s.signature_type && (
                                <span className="text-[10px] font-mono text-[var(--color-text-dim)]">
                                  {s.signature_type}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-dim)]">
                              <span>{s.confidence}%</span>
                              <span>{timeAgo(s.scanned_at)}</span>
                            </div>
                          </div>
                          {s.resolution > 0 && (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1 rounded-full bg-gray-800 overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${RESOLUTION_COLORS[s.resolution_label] || 'bg-gray-600'}`}
                                  style={{ width: `${s.resolution}%` }}
                                />
                              </div>
                              <span className="text-[9px] text-[var(--color-text-dim)] font-mono w-16 text-right">
                                {s.resolution_label?.replace('_', ' ')}
                              </span>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}

                {activeTab === 'scanners' && (
                  <div>
                    <h4 className="text-xs text-[var(--color-text-dim)] uppercase tracking-wider mb-3">
                      Top Scanners (24h)
                    </h4>
                    {zoneActivity.active_scanners.length > 0 ? (
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={zoneActivity.active_scanners} layout="vertical">
                          <XAxis
                            type="number"
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                            allowDecimals={false}
                          />
                          <YAxis
                            type="category"
                            dataKey="scanner_id"
                            tick={{ fill: '#6b7280', fontSize: 10 }}
                            axisLine={{ stroke: '#374151' }}
                            tickLine={false}
                            width={100}
                            tickFormatter={(v: string) => v.slice(0, 8) + '...'}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1f2937',
                              border: '1px solid #374151',
                              borderRadius: '6px',
                              fontSize: '12px',
                            }}
                            labelStyle={{ color: '#9ca3af' }}
                          />
                          <Bar dataKey="scan_count" fill="#10b981" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-[var(--color-text-dim)] py-4 text-center">No scanner activity recorded.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
