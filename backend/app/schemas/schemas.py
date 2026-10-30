from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from app.models.entities import UserRole, TravelClass, TicketStatus, ReservationStatus, Gender, JourneyStatus


# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.PASSENGER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    name: str
    email: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# --- Station & Train Schemas ---
class StationOut(BaseModel):
    id: int
    station_code: str
    name: str
    region: str

    class Config:
        from_attributes = True


class TrainStopOut(BaseModel):
    stop_sequence: int
    station_id: int
    station_code: str
    station_name: str
    region: str
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    distance_km: int


class TrainDetailOut(BaseModel):
    id: int
    train_number: str
    train_name: str
    source_station: StationOut
    destination_station: StationOut
    active: bool
    stops: List[TrainStopOut]

    class Config:
        from_attributes = True


# --- Journey & Inventory Schemas ---
class ClassAvailabilityOut(BaseModel):
    travel_class: TravelClass
    capacity: int
    available_seats: int
    waitlist_limit: int
    waitlist_count: int
    fare: Decimal
    version: int


class JourneySearchItem(BaseModel):
    journey_id: int
    train_id: int
    train_number: str
    train_name: str
    source_station: StationOut
    destination_station: StationOut
    travel_date: date
    departure_datetime: datetime
    arrival_datetime: datetime
    status: JourneyStatus
    availability: List[ClassAvailabilityOut]


# --- Booking Request & Response ---
class PassengerInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: Gender


class BookingCreate(BaseModel):
    journey_id: int
    travel_class: TravelClass
    passengers: List[PassengerInput] = Field(..., min_length=1, max_length=4)
    idempotency_key: Optional[str] = None


class PassengerOut(BaseModel):
    id: int
    full_name: str
    age: int
    gender: Gender
    seat_number: Optional[str]
    reservation_status: ReservationStatus
    waitlist_position: Optional[int]

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: int
    pnr: str
    user_id: int
    journey_id: int
    train_number: str
    train_name: str
    source_station_code: str
    destination_station_code: str
    travel_date: date
    travel_class: TravelClass
    passenger_count: int
    total_fare: Decimal
    status: TicketStatus
    created_at: datetime
    cancelled_at: Optional[datetime]
    passengers: List[PassengerOut]

    class Config:
        from_attributes = True


# --- Live Projections & Operational Status ---
class LiveTrainStatusOut(BaseModel):
    train_id: int
    train_number: str
    train_name: str
    platform: str
    delay_minutes: int
    status_text: str
    announcement: str
    updated_at: datetime
    is_simulated: bool = True


class AdminStatusUpdate(BaseModel):
    platform: Optional[str] = None
    delay_minutes: Optional[int] = None
    status_text: Optional[str] = None
    announcement: Optional[str] = None


# --- Outbox & Cloud Sync Health ---
class SyncHealthOut(BaseModel):
    app_profile: str
    mysql_connected: bool
    firebase_configured: bool
    firebase_status: str
    cosmos_configured: bool
    cosmos_status: str
    pending_events_count: int
    failed_events_count: int
    total_events_synced: int


class OutboxEventOut(BaseModel):
    id: int
    aggregate_id: str
    event_type: str
    version: int
    created_at: datetime
    firebase_synced: bool
    cosmos_synced: bool
    firebase_error: Optional[str]
    cosmos_error: Optional[str]
    attempts: int
