import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Train, Ticket, ShieldAlert, Radio, LogOut, User as UserIcon, LogIn, TrendingUp } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="bg-slate-900 text-white border-b-2 border-amber-500 shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Branding */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded bg-gradient-to-br from-blue-700 to-indigo-900 flex items-center justify-center border border-blue-400/30 group-hover:border-amber-400 transition-colors">
              <Train className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold tracking-tight text-xl font-display text-white">RAILSYNC</span>
                <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-amber-500 text-slate-950 font-mono">360</span>
              </div>
              <p className="text-[10px] tracking-widest text-slate-400 uppercase font-mono">Cloud Distributed Reservation</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
            <Link to="/" className="text-slate-200 hover:text-amber-400 transition-colors flex items-center space-x-1.5">
              <Train className="w-4 h-4" />
              <span>Train Search</span>
            </Link>

            <Link to="/trips" className="text-slate-200 hover:text-amber-400 transition-colors flex items-center space-x-1.5">
              <Ticket className="w-4 h-4" />
              <span>My Trips / PNR</span>
            </Link>

            <Link to="/live-status" className="text-slate-200 hover:text-amber-400 transition-colors flex items-center space-x-1.5">
              <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span>Live Radar</span>
            </Link>

            <Link to="/trends" className="text-slate-200 hover:text-amber-400 transition-colors flex items-center space-x-1.5">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span>Booking Trends</span>
            </Link>

            {isAdmin && (
              <Link 
                to="/admin" 
                className="text-amber-300 hover:text-amber-200 transition-colors flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-amber-950/40 border border-amber-500/40"
              >
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Admin Console</span>
              </Link>
            )}
          </nav>

          {/* Auth Controls & Profile */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-slate-200">{user.name}</div>
                  <div className="text-[10px] font-mono text-amber-400 uppercase">{user.role}</div>
                </div>
                <button
                  onClick={() => { logout(); navigate('/'); }}
                  className="p-2 rounded bg-slate-800 text-slate-300 hover:text-red-400 hover:bg-slate-700 transition-all text-xs flex items-center space-x-1 border border-slate-700"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 rounded text-xs font-medium text-slate-200 hover:text-white bg-slate-800 hover:bg-slate-700 transition border border-slate-700 flex items-center space-x-1"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Login</span>
                </Link>
                <Link
                  to="/register"
                  className="px-3.5 py-1.5 rounded text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 transition shadow-sm"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
