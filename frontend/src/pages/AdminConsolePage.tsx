import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, SyncHealth, TrainDetailOut } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldAlert, RefreshCw, Radio, Cloud, Database, 
  Send, CheckCircle, AlertTriangle, Layers, BarChart2
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

export const AdminConsolePage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const queryClient = useQueryClient();

  // Selected train for simulation dispatch
  const [selectedTrainId, setSelectedTrainId] = useState<number>(1);
  const [platform, setPlatform] = useState('2');
  const [delayMinutes, setDelayMinutes] = useState(15);
  const [announcement, setAnnouncement] = useState('Rescheduled due to technical signaling inspection.');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Sync health query
  const { data: syncHealth, refetch: refetchHealth, isFetching: isFetchingHealth } = useQuery<SyncHealth>({
    queryKey: ['sync-health'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/sync-health');
      return res.data;
    },
    enabled: isAdmin,
  });

  // Admin metrics query
  const { data: metrics } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/metrics');
      return res.data;
    },
    enabled: isAdmin,
  });

  // Trains query for selection
  const { data: trains = [] } = useQuery<TrainDetailOut[]>({
    queryKey: ['trains-admin'],
    queryFn: async () => {
      const res = await apiClient.get('/trains');
      return res.data;
    },
    enabled: isAdmin,
  });

  // Outbox events query
  const { data: outboxEvents = [], refetch: refetchEvents } = useQuery({
    queryKey: ['outbox-events'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/outbox-events');
      return res.data;
    },
    enabled: isAdmin,
  });

  // Simulation Update Mutation
  const updateStatusMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.put(`/admin/trains/${selectedTrainId}/status`, {
        platform,
        delay_minutes: delayMinutes,
        status_text: delayMinutes > 0 ? 'DELAYED' : 'ON TIME',
        announcement,
      });
      return res.data;
    },
    onSuccess: () => {
      setStatusMsg('Synthetic running event broadcasted to Firebase & subscribers!');
      setTimeout(() => setStatusMsg(null), 4000);
    },
  });

  // Retry outbox sync mutation
  const retrySyncMutation = useMutation({
    mutationFn: async (eventId: number) => {
      const res = await apiClient.post(`/admin/sync/retry/${eventId}`);
      return res.data;
    },
    onSuccess: () => {
      refetchHealth();
      refetchEvents();
    },
  });

  if (!isAdmin) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <ShieldAlert className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-800">Administrator Access Required</h2>
        <p className="text-xs text-slate-500 mt-1 mb-4">
          Please log in as an administrator (e.g. <code className="font-mono text-blue-900">admin@railsync360.internal</code>).
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-mono mb-2">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>CHIEF CONTROLLER & EXAMINER CONSOLE</span>
            </div>
            <h1 className="text-2xl font-bold font-display text-white">
              Multi-Cloud Synchronization & Operations Center
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Inspect transactional outbox status, broadcast delay simulations, and verify regional event partition health.
            </p>
          </div>

          <button
            onClick={() => { refetchHealth(); refetchEvents(); }}
            disabled={isFetchingHealth}
            className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 px-3.5 py-2 rounded-lg text-xs font-mono border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${isFetchingHealth ? 'animate-spin' : ''}`} />
            <span>Refresh Diagnostics</span>
          </button>
        </div>
      </div>

      {/* Cloud Connectivity Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* MySQL */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold font-mono uppercase text-slate-500">Authoritative Core</span>
            <Database className="w-4 h-4 text-blue-900" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-display">MySQL 8 (ACID)</div>
          <div className="text-xs text-emerald-600 font-mono mt-1 font-bold flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>CONNECTED & OPERATIONAL</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Host: <code className="font-mono text-slate-700">localhost:3307</code> · Strict pessimistic row locks.
          </p>
        </div>

        {/* Firebase */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold font-mono uppercase text-slate-500">Live Projections</span>
            <Radio className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-display">Firebase Realtime DB</div>
          <div className={`text-xs font-mono mt-1 font-bold flex items-center space-x-1 ${
            syncHealth?.firebase_status === 'CONNECTED' ? 'text-emerald-600' : 'text-amber-600'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              syncHealth?.firebase_status === 'CONNECTED' ? 'bg-emerald-500' : 'bg-amber-500'
            }`} />
            <span>{syncHealth?.firebase_status || 'LOCAL_FALLBACK'}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Subscribed clients receive seat counters and delays without manual refresh.
          </p>
        </div>

        {/* Azure Cosmos DB */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold font-mono uppercase text-slate-500">Distributed Records</span>
            <Cloud className="w-4 h-4 text-cyan-600" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-display">Azure Cosmos DB</div>
          <div className={`text-xs font-mono mt-1 font-bold flex items-center space-x-1 ${
            syncHealth?.cosmos_status === 'CONFIGURED' ? 'text-emerald-600' : 'text-cyan-600'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              syncHealth?.cosmos_status === 'CONFIGURED' ? 'bg-emerald-500' : 'bg-cyan-500'
            }`} />
            <span>{syncHealth?.cosmos_status || 'LOCAL_TELEMETRY'}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Partitioned by <code className="font-mono text-slate-700">/region</code> for low-latency queries.
          </p>
        </div>
      </div>

      {/* Booking Trends & Operational Analytics */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-base font-bold font-display text-slate-900 flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-blue-900" />
              <span>Real-Time Booking Trends & Reservation Analytics</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live transactional statistics calculated from authoritative MySQL ticket records.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded bg-blue-50 text-blue-900 border border-blue-200 font-bold">
              Total Tickets: {metrics?.total_tickets || 0}
            </span>
            <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              Confirmed: {metrics?.confirmed_tickets || 0}
            </span>
            <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 font-bold">
              Waitlisted: {metrics?.waitlisted_tickets || 0}
            </span>
            <span className="px-2.5 py-1 rounded bg-red-50 text-red-800 border border-red-200 font-bold">
              Cancelled: {metrics?.cancelled_tickets || 0}
            </span>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Daily Status Trend Bar Chart */}
          <div className="lg:col-span-2 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div className="text-xs font-bold font-mono text-slate-700 uppercase mb-3 flex items-center justify-between">
              <span>Daily Booking Velocity (Confirmed vs Waitlisted vs Cancelled)</span>
              <span className="text-[10px] text-slate-400 font-normal">Real transactional event log</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metrics?.daily_trends || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <Bar dataKey="confirmed" fill="#059669" name="Confirmed" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="waitlisted" fill="#d97706" name="Waitlisted" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="cancelled" fill="#dc2626" name="Cancelled" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Regional Demand Distribution */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div className="text-xs font-bold font-mono text-slate-700 uppercase mb-3">
              Regional Demand Distribution (/region)
            </div>
            <div className="space-y-3 pt-2">
              {metrics?.regional_breakdown && Object.entries(metrics.regional_breakdown).length > 0 ? (
                Object.entries(metrics.regional_breakdown).map(([region, count]) => {
                  const total = metrics.total_tickets || 1;
                  const pct = Math.round(((count as number) / total) * 100);
                  return (
                    <div key={region} className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="font-semibold text-slate-800">{region} Region</span>
                        <span className="text-slate-500">{count as number} tickets ({pct}%)</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                        <div 
                          className="h-full bg-blue-900 rounded-full transition-all duration-500" 
                          style={{ width: `${pct}%` }} 
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-slate-400 py-6 text-center font-mono">No regional events recorded yet.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Operational Simulation Control */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6 mb-8">
        <h2 className="text-base font-bold font-display text-slate-900 mb-1 flex items-center space-x-2">
          <Send className="w-4 h-4 text-amber-600" />
          <span>Operational Event Injection (Simulate Platform / Delay)</span>
        </h2>
        <p className="text-xs text-slate-500 mb-6 font-sans">
          Injected operational events immediately update the live database and broadcast to subscriber displays.
        </p>

        {statusMsg && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>{statusMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-[11px] font-bold font-mono text-slate-600 uppercase mb-1">Select Train</label>
            <select
              value={selectedTrainId}
              onChange={(e) => setSelectedTrainId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded p-2 text-xs"
            >
              {trains.map((t) => (
                <option key={t.id} value={t.id}>
                  #{t.train_number} {t.train_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-bold font-mono text-slate-600 uppercase mb-1">Platform No.</label>
            <input
              type="text"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded p-2 text-xs font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold font-mono text-slate-600 uppercase mb-1">Delay (Minutes)</label>
            <input
              type="number"
              min={0}
              max={300}
              value={delayMinutes}
              onChange={(e) => setDelayMinutes(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded p-2 text-xs font-mono"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-[11px] font-bold font-mono text-slate-600 uppercase mb-1">Station Announcement Text</label>
          <input
            type="text"
            value={announcement}
            onChange={(e) => setAnnouncement(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded p-2 text-xs"
          />
        </div>

        <button
          onClick={() => updateStatusMutation.mutate()}
          disabled={updateStatusMutation.isPending}
          className="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-5 py-2.5 rounded-lg shadow transition"
        >
          {updateStatusMutation.isPending ? 'Broadcasting...' : 'Broadcast Operational Event'}
        </button>
      </div>

      {/* Transactional Outbox Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold font-display text-slate-900 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-blue-900" />
              <span>Transactional Outbox Telemetry Log</span>
            </h2>
            <p className="text-xs text-slate-500">
              Guaranteed delivery via asynchronous dispatch worker.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded">
            {outboxEvents.length} events logged
          </span>
        </div>

        <div className="border border-slate-200 rounded-lg overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 font-mono text-slate-600 uppercase">
              <tr>
                <th className="px-3 py-2 text-left">ID</th>
                <th className="px-3 py-2 text-left">Event Type</th>
                <th className="px-3 py-2 text-left">Aggregate ID (PNR)</th>
                <th className="px-3 py-2 text-left">Firebase Sync</th>
                <th className="px-3 py-2 text-left">Cosmos Sync</th>
                <th className="px-3 py-2 text-left">Created At</th>
                <th className="px-3 py-2 text-left">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {outboxEvents.map((evt: any) => (
                <tr key={evt.id}>
                  <td className="px-3 py-2 font-mono text-slate-500">#{evt.id}</td>
                  <td className="px-3 py-2 font-mono font-bold text-slate-800">{evt.event_type}</td>
                  <td className="px-3 py-2 font-mono text-blue-900 font-bold">{evt.aggregate_id}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      evt.firebase_synced ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {evt.firebase_synced ? 'SYNCED' : 'PENDING'}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      evt.cosmos_synced ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {evt.cosmos_synced ? 'SYNCED' : 'PENDING'}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500 font-mono">
                    {new Date(evt.created_at).toLocaleTimeString()}
                  </td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => retrySyncMutation.mutate(evt.id)}
                      className="text-blue-900 hover:text-blue-700 font-semibold text-[11px] underline"
                    >
                      Retry
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
