import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, TrainDetailOut, LiveTrainStatus } from '../services/api';
import { Radio, Clock, AlertTriangle, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';

export const LiveRadarPage: React.FC = () => {
  const [selectedTrainId, setSelectedTrainId] = useState<number>(1);
  const [lastRefreshed, setLastRefreshed] = useState<string>(new Date().toLocaleTimeString());

  // Fetch trains list
  const { data: trains = [] } = useQuery<TrainDetailOut[]>({
    queryKey: ['trains-radar'],
    queryFn: async () => {
      const res = await apiClient.get('/trains');
      return res.data;
    },
  });

  // Fetch live running status
  const { data: liveStatus, refetch, isFetching } = useQuery<LiveTrainStatus>({
    queryKey: ['live-status', selectedTrainId],
    queryFn: async () => {
      const res = await apiClient.get(`/live/trains/${selectedTrainId}`);
      setLastRefreshed(new Date().toLocaleTimeString());
      return res.data;
    },
    refetchInterval: 5000, // Reactive polling interval
  });

  const selectedTrain = trains.find((t) => t.id === selectedTrainId) || trains[0];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono mb-2">
              <Radio className="w-4 h-4 animate-pulse" />
              <span>LIVE OPERATIONAL RADAR & ANNOUNCEMENTS</span>
            </div>
            <h1 className="text-2xl font-bold font-display text-white">
              Real-Time Platform & Delay Broadcast
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Synchronized simulation engine. Admin platform changes and delay injections project live to subscriber browsers.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Last Synced:</span>
            <span className="text-amber-400 font-bold">{lastRefreshed}</span>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="ml-2 text-slate-400 hover:text-white"
              title="Manual Refresh"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-amber-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Train Selector Chips */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-4 mb-6 scrollbar-thin">
        {trains.map((t) => (
          <button
            key={t.id}
            onClick={() => setSelectedTrainId(t.id)}
            className={`px-4 py-2 rounded-lg text-xs font-mono font-semibold whitespace-nowrap transition border ${
              t.id === selectedTrainId
                ? 'bg-blue-900 text-white border-amber-400 shadow'
                : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
            }`}
          >
            #{t.train_number} {t.train_name.split(' ')[0]}
          </button>
        ))}
      </div>

      {/* Live Status Display Card */}
      {selectedTrain && liveStatus && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6 mb-8">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-6">
            <div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-bold">
                #{selectedTrain.train_number}
              </span>
              <h2 className="text-lg font-bold text-slate-900 mt-1">{selectedTrain.train_name}</h2>
              <p className="text-xs text-slate-500">
                {selectedTrain.source_station.name} ({selectedTrain.source_station.station_code}) → {selectedTrain.destination_station.name} ({selectedTrain.destination_station.station_code})
              </p>
            </div>

            {/* Status Indicators */}
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Assigned Platform</div>
                <div className="text-2xl font-black font-mono text-slate-900">
                  PF-{liveStatus.platform}
                </div>
              </div>

              <div className="h-8 w-px bg-slate-200 mx-1" />

              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-400 uppercase">Running Status</div>
                <span className={`inline-block px-2.5 py-1 rounded text-xs font-bold font-mono ${
                  liveStatus.delay_minutes > 0
                    ? 'bg-red-100 text-red-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {liveStatus.delay_minutes > 0 ? `LATE BY ${liveStatus.delay_minutes} MIN` : 'ON TIME'}
                </span>
              </div>
            </div>
          </div>

          {/* Announcement Ticker */}
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mb-6 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-xs font-bold font-mono text-amber-900 uppercase tracking-wider">
                Official Station Announcement (Simulated Telemetry)
              </div>
              <div className="text-sm font-medium text-slate-800 mt-0.5 font-sans">
                {liveStatus.announcement}
              </div>
            </div>
          </div>

          {/* Route Sequence & Halts */}
          <div>
            <h3 className="text-xs font-bold font-mono uppercase text-slate-500 mb-3">
              Scheduled Route Sequence & Timing Snapshots
            </h3>
            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {selectedTrain.stops.map((stop) => (
                <div key={stop.stop_sequence} className="relative flex items-center justify-between text-xs">
                  <div className="absolute -left-6 w-4 h-4 rounded-full bg-blue-900 border-2 border-white shadow-sm flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  </div>
                  <div>
                    <span className="font-bold text-slate-900">{stop.station_name}</span>
                    <span className="text-slate-500 font-mono ml-1.5">({stop.station_code})</span>
                    <span className="text-[10px] text-slate-400 ml-2 font-mono">{stop.distance_km} km</span>
                  </div>
                  <div className="font-mono text-slate-600 text-right">
                    {stop.arrival_time ? `Arr: ${stop.arrival_time}` : 'Origin'}
                    {stop.departure_time ? ` · Dep: ${stop.departure_time}` : ' · Final Destination'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
