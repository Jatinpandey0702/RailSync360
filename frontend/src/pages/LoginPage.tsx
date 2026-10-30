import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../services/api';
import { LogIn, Lock, Mail, AlertCircle, Train } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('passenger@example.com');
  const [password, setPassword] = useState('Passenger123!');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await apiClient.post('/auth/login', { email, password });
      login(res.data.access_token, {
        id: 0,
        name: res.data.name,
        email: res.data.email,
        role: res.data.role,
      });
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (role: 'PASSENGER' | 'ADMIN') => {
    if (role === 'PASSENGER') {
      setEmail('passenger@example.com');
      setPassword('Passenger123!');
    } else {
      setEmail('admin@railsync360.internal');
      setPassword('AdminPass2026!');
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-900 text-amber-400 flex items-center justify-center mx-auto mb-3 shadow">
            <Train className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold font-display text-slate-900">Sign In to RailSync 360</h1>
          <p className="text-xs text-slate-500 mt-1">Access verified reservations and real-time live availability</p>
        </div>

        {/* Quick Fill Demo Credentials */}
        <div className="mb-6 bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs">
          <span className="font-mono text-[10px] text-slate-500 uppercase block mb-1.5 font-bold">Quick Demo Login:</span>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => handleQuickFill('PASSENGER')}
              className="px-2.5 py-1 rounded bg-white border border-slate-300 hover:border-blue-600 text-slate-700 text-[11px] font-medium"
            >
              Passenger Demo
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('ADMIN')}
              className="px-2.5 py-1 rounded bg-amber-100 border border-amber-300 hover:border-amber-600 text-amber-900 text-[11px] font-bold"
            >
              Admin Controller
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold font-mono text-slate-600 uppercase mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold font-mono text-slate-600 uppercase mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold text-xs py-2.5 rounded-lg shadow transition flex items-center justify-center space-x-2 mt-2"
          >
            <LogIn className="w-4 h-4" />
            <span>{isLoading ? 'Verifying...' : 'Sign In'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
