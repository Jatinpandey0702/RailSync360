import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiClient, Station, JourneySearchItem } from '../services/api';
import { Search, Calendar, Users, Train, Clock, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';

export const SearchPage: React.FC = () => {
  const navigate = useNavigate();

  // Search parameters
  const [source, setSource] = useState('NDLS');
  const [destination, setDestination] = useState('BCT');
  const [travelDate, setTravelDate] = useState(() => {
    const d = new Date();
    return d.toISOString().split('T')[0];
  });
  const [passengerCount, setPassengerCount] = useState(1);

  // Fetch stations for dropdowns
  const { data: stations = [] } = useQuery<Station[]>({
    queryKey: ['stations'],
    queryFn: async () => {
      const res = await apiClient.get('/stations');
      return res.data;
    },
  });

  // Query train journeys
  const { data: journeys = [], isLoading, error, refetch } = useQuery<JourneySearchItem[]>({
    queryKey: ['journeys', source, destination, travelDate],
    queryFn: async () => {
      const res = await apiClient.get('/journeys/search', {
        params: {
          source,
          destination,
          travel_date: travelDate,
        },
      });
      return res.data;
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  const handleBookClick = (journeyId: number, travelClass: 'AC' | 'GENERAL') => {
    navigate(`/book?journeyId=${journeyId}&travelClass=${travelClass}&passengers=${passengerCount}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white relative overflow-hidden shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 bg-gradient-to-l from-amber-400 to-transparent pointer-events-none rail-track-line" />
        <div className="max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono mb-3">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            <span>High-Throughput Authoritative Core</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-white mb-2">
            National Railway Express Reservation
          </h1>
          <p className="text-sm text-slate-300 font-sans leading-relaxed">
            Instant ticket booking, verified seat availability, and live platform status updates across nationwide express routes.
          </p>
        </div>
      </div>

      {/* Railway Search Form */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-md p-6 mb-8">
        <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          {/* Source Station */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 font-mono">
              From Station
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm font-medium focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
            >
              {stations.map((st) => (
                <option key={st.id} value={st.station_code}>
                  {st.name} ({st.station_code}) — {st.region}
                </option>
              ))}
            </select>
          </div>

          {/* Destination Station */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 font-mono">
              To Station
            </label>
            <select
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm font-medium focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
            >
              {stations.map((st) => (
                <option key={st.id} value={st.station_code}>
                  {st.name} ({st.station_code}) — {st.region}
                </option>
              ))}
            </select>
          </div>

          {/* Date Picker */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 font-mono flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Travel Date (Next 7 Days)</span>
            </label>
            <input
              type="date"
              value={travelDate}
              onChange={(e) => setTravelDate(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm font-medium focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
            />
          </div>

          {/* Search Button */}
          <div>
            <button
              type="submit"
              className="w-full bg-blue-900 hover:bg-blue-800 text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center space-x-2 transition shadow"
            >
              <Search className="w-4 h-4" />
              <span>Find Trains</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900 font-display flex items-center space-x-2">
            <Train className="w-5 h-5 text-blue-900" />
            <span>Available Scheduled Journeys</span>
          </h2>
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded">
            {journeys.length} service(s) found
          </span>
        </div>

        {isLoading ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
            <div className="w-8 h-8 border-4 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm font-medium">Scanning live journey inventory...</p>
          </div>
        ) : journeys.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Train className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-800 mb-1">No Direct Scheduled Trains Found</h3>
            <p className="text-sm text-slate-500 max-w-lg mx-auto mb-4">
              No service matches this station pair or direction on {travelDate}. Trains run across routes such as:
            </p>
            <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
              {[
                { s: 'NDLS', d: 'BCT', label: 'NDLS → BCT' },
                { s: 'HWH', d: 'NDLS', label: 'HWH → NDLS' },
                { s: 'NDLS', d: 'MAS', label: 'NDLS → MAS' },
                { s: 'SBC', d: 'NDLS', label: 'SBC → NDLS' },
                { s: 'NDLS', d: 'CNB', label: 'NDLS → CNB' },
                { s: 'CNB', d: 'NDLS', label: 'CNB → NDLS' },
                { s: 'BBR', d: 'BCT', label: 'BBR → BCT' },
              ].map((route) => (
                <button
                  key={route.label}
                  type="button"
                  onClick={() => {
                    setSource(route.s);
                    setDestination(route.d);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-800 text-xs font-semibold hover:bg-blue-100 transition border border-blue-200"
                >
                  {route.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {journeys.map((j) => (
              <div
                key={j.journey_id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition p-6"
              >
                {/* Train Header Info */}
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-900">
                        #{j.train_number}
                      </span>
                      <h3 className="text-base font-bold text-slate-900">{j.train_name}</h3>
                    </div>
                    <p className="text-xs text-slate-500">
                      Standard Express Route · Source: {j.source_station.name} ({j.source_station.station_code}) · Destination: {j.destination_station.name} ({j.destination_station.station_code})
                    </p>
                  </div>

                  {/* Timings */}
                  <div className="text-right flex items-center space-x-4">
                    <div>
                      <div className="text-xs font-mono text-slate-400">Departure</div>
                      <div className="text-sm font-bold text-slate-800">
                        {new Date(j.departure_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                    <div>
                      <div className="text-xs font-mono text-slate-400">Arrival</div>
                      <div className="text-sm font-bold text-slate-800">
                        {new Date(j.arrival_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Class Availability & Booking Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {j.availability.map((inv) => {
                    const isAvailable = inv.available_seats > 0;
                    const isWLAvailable = !isAvailable && inv.waitlist_count < inv.waitlist_limit;
                    const isFull = !isAvailable && !isWLAvailable;

                    return (
                      <div
                        key={inv.travel_class}
                        className={`rounded-lg p-4 border transition ${
                          isAvailable
                            ? 'border-emerald-200 bg-emerald-50/40'
                            : isWLAvailable
                            ? 'border-amber-200 bg-amber-50/40'
                            : 'border-slate-200 bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-sm tracking-wide text-slate-900 font-mono">
                            {inv.travel_class === 'AC' ? 'AC Tier (Executive / 2-Tier)' : 'General / Second Sitting'}
                          </span>
                          <span className="text-base font-extrabold text-slate-900 font-mono">
                            ₹{inv.fare.toLocaleString()}
                          </span>
                        </div>

                        {/* Status Matrix */}
                        <div className="flex items-center justify-between text-xs mb-3">
                          <span className="text-slate-500">Seat Status:</span>
                          {isAvailable ? (
                            <span className="font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-mono">
                              AVAILABLE — {inv.available_seats} SEATS
                            </span>
                          ) : isWLAvailable ? (
                            <span className="font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded font-mono">
                              WAITLIST — WL {inv.waitlist_count + 1}
                            </span>
                          ) : (
                            <span className="font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded font-mono">
                              REGISTRATION CLOSED (FULL)
                            </span>
                          )}
                        </div>

                        {/* Booking CTA */}
                        <button
                          onClick={() => handleBookClick(j.journey_id, inv.travel_class)}
                          disabled={isFull}
                          className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition ${
                            isFull
                              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                              : 'bg-blue-900 hover:bg-blue-800 text-white shadow-sm'
                          }`}
                        >
                          <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                          <span>{isAvailable ? 'Book Confirmed Seat' : isWLAvailable ? 'Book Waitlist Ticket' : 'Full Capacity'}</span>
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
