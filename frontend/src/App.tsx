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
                  RailSync 360 · Modern Railway Reservation & Real-Time Booking System
                </div>
                <div className="text-[11px] text-slate-400">
                  Reliable Passenger Journeys · Live Availability · Fast & Secure Ticketing
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
