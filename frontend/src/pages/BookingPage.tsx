import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient, PassengerInput, Ticket } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, UserPlus, Trash2, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';

export const BookingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const journeyId = Number(searchParams.get('journeyId'));
  const travelClass = (searchParams.get('travelClass') as 'AC' | 'GENERAL') || 'AC';

  // Passenger state list
  const [passengers, setPassengers] = useState<PassengerInput[]>([
    { full_name: user?.name || '', age: 28, gender: 'MALE' }
  ]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [bookedTicket, setBookedTicket] = useState<Ticket | null>(null);

  const addPassenger = () => {
    if (passengers.length >= 4) return;
    setPassengers([...passengers, { full_name: '', age: 30, gender: 'MALE' }]);
  };

  const removePassenger = (index: number) => {
    if (passengers.length <= 1) return;
    setPassengers(passengers.filter((_, i) => i !== index));
  };

  const updatePassenger = (index: number, field: keyof PassengerInput, value: any) => {
    const updated = [...passengers];
    updated[index] = { ...updated[index], [field]: value };
    setPassengers(updated);
  };

  // Mutation for booking transaction
  const bookingMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      const res = await apiClient.post('/bookings', {
        journey_id: journeyId,
        travel_class: travelClass,
        passengers: passengers
      });
      return res.data;
    },
    onSuccess: (data: Ticket) => {
      setBookedTicket(data);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || 'Failed to complete booking transaction.';
      setErrorMessage(msg);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      navigate('/login');
      return;
    }
    bookingMutation.mutate();
  };

  // Success Confirmation Screen
  if (bookedTicket) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl border-2 border-emerald-500 shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-emerald-600 text-white p-6 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-8 h-8 text-white" />
              <div>
                <h2 className="text-xl font-bold font-display">Booking Confirmed Successfully</h2>
                <p className="text-xs text-emerald-100 font-mono">Durable ACID Transaction Committed to MySQL Core</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-mono tracking-wider text-emerald-200">System PNR</div>
              <div className="text-xl font-extrabold font-mono tracking-widest text-amber-300">{bookedTicket.pnr}</div>
            </div>
          </div>

          {/* Details */}
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 font-mono text-xs">
              <div>
                <span className="text-slate-400 block">Train No & Name</span>
                <span className="font-bold text-slate-800">{bookedTicket.train_number} - {bookedTicket.train_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Travel Date</span>
                <span className="font-bold text-slate-800">{bookedTicket.travel_date}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Class</span>
                <span className="font-bold text-slate-800">{bookedTicket.travel_class}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Total Fare Paid (Simulated)</span>
                <span className="font-bold text-emerald-700">₹{bookedTicket.total_fare}</span>
              </div>
            </div>

            {/* Allocated Passenger Seats */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-3 font-mono">Passenger & Seat Assignment Details</h3>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                  <thead className="bg-slate-100 font-mono text-slate-600 uppercase">
                    <tr>
                      <th className="px-4 py-2.5">#</th>
                      <th className="px-4 py-2.5">Passenger Name</th>
                      <th className="px-4 py-2.5">Age / Gender</th>
                      <th className="px-4 py-2.5">Status</th>
                      <th className="px-4 py-2.5">Assigned Seat</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {bookedTicket.passengers.map((p, idx) => (
                      <tr key={p.id}>
                        <td className="px-4 py-3 font-mono">{idx + 1}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{p.full_name}</td>
                        <td className="px-4 py-3 text-slate-500">{p.age} Yrs / {p.gender}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded font-mono font-bold text-[11px] ${
                            p.reservation_status === 'CNF' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                          }`}>
                            {p.reservation_status === 'CNF' ? 'CONFIRMED' : `WAITLIST (WL-${p.waitlist_position})`}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-blue-900">
                          {p.seat_number || 'N/A (Waitlisted)'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                onClick={() => navigate('/trips')}
                className="bg-blue-900 text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-blue-800 transition"
              >
                Go to My Trips
              </button>
              <button
                onClick={() => navigate('/')}
                className="bg-slate-100 text-slate-700 text-xs font-semibold px-4 py-2 rounded-lg hover:bg-slate-200 transition"
              >
                Book Another Ticket
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center space-x-1 text-xs font-medium text-slate-500 hover:text-slate-800 mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to search results</span>
      </button>

      <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6">
        <div className="border-b border-slate-200 pb-4 mb-6">
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded bg-blue-100 text-blue-900 text-xs font-mono mb-2">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-800" />
            <span>Guaranteed Seat Allocation</span>
          </div>
          <h1 className="text-xl font-bold font-display text-slate-900">Passenger Details & Reservation</h1>
          <p className="text-xs text-slate-500 mt-1">
            Journey ID #{journeyId} · Travel Class: <strong className="text-slate-700">{travelClass}</strong> · Simulated Checkout
          </p>
        </div>

        {errorMessage && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start space-x-3 text-red-800 text-xs">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-bold">Reservation Failed</div>
              <div>{errorMessage}</div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            {passengers.map((p, idx) => (
              <div key={idx} className="p-4 rounded-lg border border-slate-200 bg-slate-50 relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold font-mono uppercase text-slate-600">Passenger {idx + 1}</span>
                  {passengers.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removePassenger(idx)}
                      className="text-red-500 hover:text-red-700 text-xs flex items-center space-x-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Remove</span>
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ramesh Kumar"
                      value={p.full_name}
                      onChange={(e) => updatePassenger(idx, 'full_name', e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded p-2 text-xs focus:ring-1 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Age</label>
                    <input
                      type="number"
                      required
                      min={1}
                      max={120}
                      value={p.age}
                      onChange={(e) => updatePassenger(idx, 'age', Number(e.target.value))}
                      className="w-full bg-white border border-slate-300 rounded p-2 text-xs focus:ring-1 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Gender</label>
                    <select
                      value={p.gender}
                      onChange={(e) => updatePassenger(idx, 'gender', e.target.value as any)}
                      className="w-full bg-white border border-slate-300 rounded p-2 text-xs focus:ring-1 focus:ring-blue-600"
                    >
                      <option value="MALE">Male</option>
                      <option value="FEMALE">Female</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {passengers.length < 4 && (
            <button
              type="button"
              onClick={addPassenger}
              className="text-xs font-semibold text-blue-900 hover:text-blue-700 flex items-center space-x-1.5 py-1"
            >
              <UserPlus className="w-4 h-4" />
              <span>Add Another Passenger (Max 4)</span>
            </button>
          )}

          <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
            <div className="text-xs text-slate-500">
              Payment is <strong>simulated</strong> for demonstration. Real cards are never charged.
            </div>
            <button
              type="submit"
              disabled={bookingMutation.isPending}
              className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs px-6 py-2.5 rounded-lg shadow transition flex items-center space-x-2"
            >
              {bookingMutation.isPending ? (
                <span>Executing SQL Lock...</span>
              ) : (
                <span>Confirm Reservation ({passengers.length} Passenger{passengers.length > 1 ? 's' : ''})</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
