import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { 
  BarChart2, TrendingUp, MapPin, Ticket, ShieldCheck, 
  Calendar, Layers, CheckCircle2, Clock, AlertTriangle
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

interface BookingTrendsData {
  total_tickets: number;
  confirmed_tickets: number;
  waitlisted_tickets: number;
  cancelled_tickets: number;
  regional_breakdown: Record<string, number>;
  daily_trends: Array<{
    date: string;
    confirmed: number;
    waitlisted: number;
    cancelled: number;
    total: number;
  }>;
  route_demand: Array<{
    route: string;
    demand: number;
    region: string;
  }>;
  class_breakdown: Array<{
    name: string;
    value: number;
  }>;
}

export const BookingTrendsPage: React.FC = () => {
  const { data: trends, isLoading } = useQuery<BookingTrendsData>({
    queryKey: ['public-booking-trends'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/booking-trends');
      return res.data;
    },
    refetchInterval: 5000,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white relative overflow-hidden shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 bg-gradient-to-l from-amber-400 to-transparent pointer-events-none rail-track-line" />
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono mb-3">
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>Public Passenger Telemetry & Historical Trends</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-white mb-2">
            Booking Trends & Regional Demand Insights
          </h1>
          <p className="text-sm text-slate-300 font-sans leading-relaxed">
            Transparent reservation statistics, historical demand distribution, and regional passenger occupancy computed from authoritative records.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2 font-mono text-xs">
            <span>Total Bookings</span>
            <Ticket className="w-4 h-4 text-blue-900" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">
            {trends?.total_tickets || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-sans">All-time reservation volume</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2 font-mono text-xs">
            <span>Confirmed Seats</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-700">
            {trends?.confirmed_tickets || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-sans">Guaranteed berths allocated</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2 font-mono text-xs">
            <span>Waitlist Queue</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black font-mono text-amber-700">
            {trends?.waitlisted_tickets || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-sans">Eligible for FIFO cancellation upgrade</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2 font-mono text-xs">
            <span>Cancelled Tickets</span>
            <AlertTriangle className="w-4 h-4 text-red-600" />
          </div>
          <div className="text-2xl font-black font-mono text-red-700">
            {trends?.cancelled_tickets || 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-sans">Freed seats returned to inventory</p>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Booking Velocity Over Time */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold font-display text-slate-900 flex items-center space-x-2">
                <BarChart2 className="w-4 h-4 text-blue-900" />
                <span>Booking Velocity & Demand Distribution</span>
              </h2>
              <p className="text-xs text-slate-500">Volume breakdown of confirmed, waitlisted, and cancelled tickets over time.</p>
            </div>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded">Live Query</span>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends?.daily_trends || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
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

        {/* Regional Distribution (/region) */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="mb-4 border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold font-display text-slate-900 flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-blue-900" />
              <span>Regional Demand (/region)</span>
            </h2>
            <p className="text-xs text-slate-500">Geographic booking concentration by railway zone.</p>
          </div>

          <div className="space-y-4 pt-2">
            {trends?.regional_breakdown && Object.entries(trends.regional_breakdown).length > 0 ? (
              Object.entries(trends.regional_breakdown).map(([region, count]) => {
                const total = trends.total_tickets || 1;
                const pct = Math.round(((count as number) / total) * 100);
                return (
                  <div key={region} className="space-y-1.5">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="font-semibold text-slate-800">{region} Region</span>
                      <span className="text-slate-500 font-bold">{count} tickets ({pct}%)</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
                      <div 
                        className="h-full bg-blue-900 rounded-full transition-all duration-500" 
                        style={{ width: `${pct}%` }} 
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-xs text-slate-400 py-8 text-center font-mono">
                No regional records registered yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Popular Route Demand Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-bold font-display text-slate-900 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-blue-900" />
              <span>Key Route Occupancy & Demand Indicators</span>
            </h2>
            <p className="text-xs text-slate-500">Aggregate occupancy and booking demand across top express train routes.</p>
          </div>
        </div>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 font-mono text-slate-600 uppercase">
              <tr>
                <th className="px-4 py-2.5 text-left">Route & Service</th>
                <th className="px-4 py-2.5 text-left">Zone / Region</th>
                <th className="px-4 py-2.5 text-left">Historical Demand Index</th>
                <th className="px-4 py-2.5 text-left">Occupancy Indicator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {(trends?.route_demand || []).map((rd, idx) => (
                <tr key={idx}>
                  <td className="px-4 py-3 font-semibold text-slate-900">{rd.route}</td>
                  <td className="px-4 py-3 text-slate-500 font-mono">{rd.region}</td>
                  <td className="px-4 py-3 font-mono font-bold text-blue-900">{rd.demand} / 100</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-emerald-100 text-emerald-800">
                      HIGH OCCUPANCY
                    </span>
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
