import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, Ticket } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Ticket as TicketIcon, Search, AlertCircle, XCircle, CheckCircle2, Clock } from 'lucide-react';

export const TripsPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [pnrSearch, setPnrSearch] = useState('');
  const [searchedTicket, setSearchedTicket] = useState<Ticket | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // My Trips Query
  const { data: myTickets = [], isLoading } = useQuery<Ticket[]>({
    queryKey: ['my-tickets'],
    queryFn: async () => {
      const res = await apiClient.get('/bookings/me');
      return res.data;
    },
    enabled: !!user,
  });

  // Cancel Booking Mutation
  const cancelMutation = useMutation({
    mutationFn: async (pnr: string) => {
      const res = await apiClient.post(`/bookings/${pnr}/cancel`);
      return res.data;
    },
    onSuccess: (updatedTicket: Ticket) => {
      queryClient.invalidateQueries({ queryKey: ['my-tickets'] });
      if (searchedTicket?.pnr === updatedTicket.pnr) {
        setSearchedTicket(updatedTicket);
      }
    },
  });

  const handleSearchPnr = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pnrSearch.trim()) return;
    setSearchError(null);
    setSearchedTicket(null);

    try {
      const res = await apiClient.get(`/bookings/${pnrSearch.trim().toUpperCase()}`);
      setSearchedTicket(res.data);
    } catch (err: any) {
      setSearchError(err.response?.data?.detail || 'Ticket not found or unauthorized.');
    }
  };

  const handleCancel = (pnr: string) => {
    if (window.confirm(`Are you sure you want to cancel ticket ${pnr}? If waitlisted passengers exist, the next passenger in queue will be automatically promoted.`)) {
      cancelMutation.mutate(pnr);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold font-display text-slate-900">My Trips & PNR Lookup</h1>
          <p className="text-xs text-slate-500 font-sans">
            Inspect reservation status, seat allocations, or cancel with automatic FIFO waitlist promotion.
          </p>
        </div>

        {/* PNR Search Form */}
        <form onSubmit={handleSearchPnr} className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Enter 10-char PNR..."
            value={pnrSearch}
            onChange={(e) => setPnrSearch(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-mono uppercase focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
          <button
            type="submit"
            className="bg-blue-900 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-blue-800 transition flex items-center space-x-1"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Lookup</span>
          </button>
        </form>
      </div>

      {/* Searched Ticket Result Card */}
      {searchedTicket && (
        <div className="mb-8">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 font-mono">
            Direct PNR Lookup Result
          </div>
          <TicketCard ticket={searchedTicket} onCancel={handleCancel} isCancelling={cancelMutation.isPending} />
        </div>
      )}

      {searchError && (
        <div className="mb-8 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{searchError}</span>
        </div>
      )}

      {/* Authenticated User Bookings */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 font-mono">
          Your Confirmed & Waitlisted Bookings ({myTickets.length})
        </h2>

        {!user ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
            Please log in to view your complete booking history.
          </div>
        ) : isLoading ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
            Loading your bookings...
          </div>
        ) : myTickets.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
            No booking records found for your account. Use the search page to reserve a seat.
          </div>
        ) : (
          myTickets.map((t) => (
            <TicketCard key={t.id} ticket={t} onCancel={handleCancel} isCancelling={cancelMutation.isPending} />
          ))
        )}
      </div>
    </div>
  );
};

const TicketCard: React.FC<{
  ticket: Ticket;
  onCancel: (pnr: string) => void;
  isCancelling: boolean;
}> = ({ ticket, onCancel, isCancelling }) => {
  const isCancelled = ticket.status === 'CANCELLED';
  const isWaitlisted = ticket.status === 'WAITLISTED';

  return (
    <div className={`rounded-xl border shadow-sm p-6 bg-white transition ${
      isCancelled ? 'opacity-60 border-slate-200' : 'border-slate-200 hover:border-slate-300'
    }`}>
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-900">
              PNR: {ticket.pnr}
            </span>
            <span className={`px-2 py-0.5 rounded font-mono font-bold text-[11px] ${
              isCancelled
                ? 'bg-red-100 text-red-800'
                : isWaitlisted
                ? 'bg-amber-100 text-amber-800'
                : 'bg-emerald-100 text-emerald-800'
            }`}>
              {ticket.status}
            </span>
          </div>
          <h3 className="text-base font-bold text-slate-900">
            #{ticket.train_number} — {ticket.train_name}
          </h3>
          <p className="text-xs text-slate-500">
            Route: {ticket.source_station_code} → {ticket.destination_station_code} · Date: {ticket.travel_date} · Class: {ticket.travel_class}
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs text-slate-400 font-mono">Fare Paid</div>
          <div className="text-base font-bold text-slate-900 font-mono">₹{ticket.total_fare}</div>
          {!isCancelled && (
            <button
              onClick={() => onCancel(ticket.pnr)}
              disabled={isCancelling}
              className="mt-2 text-xs font-semibold text-red-600 hover:text-red-700 underline"
            >
              Cancel Reservation
            </button>
          )}
        </div>
      </div>

      {/* Passengers Table */}
      <div className="border border-slate-100 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-slate-100 text-xs">
          <thead className="bg-slate-50 text-slate-500 font-mono">
            <tr>
              <th className="px-3 py-2 text-left">Passenger</th>
              <th className="px-3 py-2 text-left">Age / Gender</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Seat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {ticket.passengers.map((p) => (
              <tr key={p.id}>
                <td className="px-3 py-2 font-medium text-slate-800">{p.full_name}</td>
                <td className="px-3 py-2 text-slate-500">{p.age} / {p.gender}</td>
                <td className="px-3 py-2">
                  <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                    p.reservation_status === 'CNF'
                      ? 'bg-emerald-100 text-emerald-800'
                      : p.reservation_status === 'WL'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {p.reservation_status === 'CNF' ? 'CONFIRMED' : p.reservation_status === 'WL' ? `WL ${p.waitlist_position}` : 'CANCELLED'}
                  </span>
                </td>
                <td className="px-3 py-2 font-mono font-bold text-blue-900">
                  {p.seat_number || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
