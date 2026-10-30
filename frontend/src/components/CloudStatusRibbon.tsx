import React from 'react';
import { Database, Radio, Cloud, Server } from 'lucide-react';

interface Props {
  profile?: string;
  firebaseActive?: boolean;
  cosmosActive?: boolean;
}

export const CloudStatusRibbon: React.FC<Props> = ({
  profile = 'LOCAL_DEMO',
  firebaseActive = false,
  cosmosActive = false,
}) => {
  return (
    <div className="bg-slate-900 border-b border-slate-800 text-[11px] font-mono text-slate-400 py-1.5 px-4 shadow-inner">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Core Profile */}
        <div className="flex items-center space-x-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-slate-300 font-semibold flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span>MySQL 8 Core:</span>
          </span>
          <span className="text-emerald-400 font-bold">AUTHORITATIVE ACID ({profile})</span>
        </div>

        {/* Cloud Store Diagnostics */}
        <div className="flex items-center space-x-4">
          {/* Firebase RTDB */}
          <div className="flex items-center space-x-1.5">
            <Radio className={`w-3 h-3 ${firebaseActive ? 'text-amber-400 animate-pulse' : 'text-slate-500'}`} />
            <span>Firebase RTDB:</span>
            {firebaseActive ? (
              <span className="text-amber-400 font-semibold">SUBSCRIBED PUSH</span>
            ) : (
              <span className="text-slate-500 bg-slate-800 px-1 rounded">LOCAL FALLBACK</span>
            )}
          </div>

          {/* Azure Cosmos DB */}
          <div className="flex items-center space-x-1.5">
            <Cloud className={`w-3 h-3 ${cosmosActive ? 'text-cyan-400' : 'text-slate-500'}`} />
            <span>Cosmos NoSQL:</span>
            {cosmosActive ? (
              <span className="text-cyan-400 font-semibold">PARTITIONED (/region)</span>
            ) : (
              <span className="text-slate-500 bg-slate-800 px-1 rounded">LOCAL OUTBOX TELEMETRY</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
