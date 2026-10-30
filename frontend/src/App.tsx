import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { CloudStatusRibbon } from './components/CloudStatusRibbon';
import { SearchPage } from './pages/SearchPage';
import { BookingPage } from './pages/BookingPage';
import { TripsPage } from './pages/TripsPage';
import { LiveRadarPage } from './pages/LiveRadarPage';
import { AdminConsolePage } from './pages/AdminConsolePage';
import { BookingTrendsPage } from './pages/BookingTrendsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
            <CloudStatusRibbon />
            <Navbar />
            
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<SearchPage />} />
                <Route path="/book" element={<BookingPage />} />
                <Route path="/trips" element={<TripsPage />} />
                <Route path="/trends" element={<BookingTrendsPage />} />
                <Route path="/live-status" element={<LiveRadarPage />} />
                <Route path="/admin" element={<AdminConsolePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
              </Routes>
            </main>

            {/* System Architecture Footer */}
            <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 py-6 text-xs font-mono">
              <div className="max-w-7xl mx-auto px-4 text-center space-y-2">
                <div className="text-slate-300 font-semibold">
                  RailSync 360 · Cloud-Based Railway Reservation, Live Seat Availability and Distributed Records System
                </div>
                <div className="text-[11px] text-amber-400">
                  Demonstration Prototype · Not affiliated with Indian Railways or IRCTC
                </div>
                <div className="text-[10px] text-slate-500">
                  Multi-Store Architecture: AWS RDS MySQL 8 (Transactional Core) + Firebase RTDB (Live Projections) + Azure Cosmos DB (Distributed Regional NoSQL)
                </div>
              </div>
            </footer>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
