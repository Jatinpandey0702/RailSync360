import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('railsync_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Type definitions
export interface Station {
  id: number;
  station_code: string;
  name: string;
  region: string;
}

export interface TrainStop {
  stop_sequence: number;
  station_id: number;
  station_code: string;
  station_name: string;
  region: string;
  arrival_time?: string;
  departure_time?: string;
  distance_km: number;
}

export interface TrainDetailOut {
  id: number;
  train_number: string;
  train_name: string;
  source_station: Station;
  destination_station: Station;
  active: boolean;
  stops: TrainStop[];
}

export interface ClassAvailability {
  travel_class: 'AC' | 'GENERAL';
  capacity: number;
  available_seats: number;
  waitlist_limit: number;
  waitlist_count: number;
  fare: number;
  version: number;
}

export interface JourneySearchItem {
  journey_id: number;
  train_id: number;
  train_number: string;
  train_name: string;
  source_station: Station;
  destination_station: Station;
  travel_date: string;
  departure_datetime: string;
  arrival_datetime: string;
  status: string;
  availability: ClassAvailability[];
}

export interface PassengerInput {
  full_name: string;
  age: number;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
}

export interface Ticket {
  id: number;
  pnr: string;
  user_id: number;
  journey_id: number;
  train_number: string;
  train_name: string;
  source_station_code: string;
  destination_station_code: string;
  travel_date: string;
  travel_class: 'AC' | 'GENERAL';
  passenger_count: number;
  total_fare: number;
  status: 'CONFIRMED' | 'WAITLISTED' | 'CANCELLED';
  created_at: string;
  cancelled_at?: string;
  passengers: Array<{
    id: number;
    full_name: string;
    age: number;
    gender: string;
    seat_number?: string;
    reservation_status: 'CNF' | 'WL' | 'CAN';
    waitlist_position?: number;
  }>;
}

export interface LiveTrainStatus {
  train_id: number;
  train_number: string;
  train_name: string;
  platform: string;
  delay_minutes: number;
  status_text: string;
  announcement: string;
  updated_at: string;
  is_simulated: boolean;
}

export interface SyncHealth {
  app_profile: string;
  mysql_connected: boolean;
  firebase_configured: boolean;
  firebase_status: string;
  cosmos_configured: boolean;
  cosmos_status: string;
  pending_events_count: number;
  failed_events_count: number;
  total_events_synced: number;
}
