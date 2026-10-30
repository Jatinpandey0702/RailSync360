import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, 
    Numeric, ForeignKey, Enum, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    PASSENGER = "PASSENGER"
    ADMIN = "ADMIN"


class TravelClass(str, enum.Enum):
    AC = "AC"
    GENERAL = "GENERAL"


class JourneyStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TicketStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


class ReservationStatus(str, enum.Enum):
    CNF = "CNF"
    WL = "WL"
    CAN = "CAN"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PASSENGER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tickets = relationship("Ticket", back_populates="user")


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False, index=True)  # e.g., 'Northern', 'Western', 'Southern'


class Train(Base):
    __tablename__ = "trains"

    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String(10), unique=True, index=True, nullable=False)
    train_name = Column(String(150), nullable=False)
    source_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    destination_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    source_station = relationship("Station", foreign_keys=[source_station_id])
    destination_station = relationship("Station", foreign_keys=[destination_station_id])
    stops = relationship("TrainStop", back_populates="train", cascade="all, delete-orphan", order_by="TrainStop.stop_sequence")
    journeys = relationship("TrainJourney", back_populates="train", cascade="all, delete-orphan")


class TrainStop(Base):
    __tablename__ = "train_stops"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id", ondelete="CASCADE"), nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    stop_sequence = Column(Integer, nullable=False)
    arrival_time = Column(Time, nullable=True)
    departure_time = Column(Time, nullable=True)
    distance_km = Column(Integer, default=0, nullable=False)

    train = relationship("Train", back_populates="stops")
    station = relationship("Station")

    __table_args__ = (
        UniqueConstraint("train_id", "stop_sequence", name="uq_train_stop_sequence"),
        Index("ix_train_stop_station", "train_id", "station_id"),
    )


class TrainJourney(Base):
    __tablename__ = "train_journeys"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id", ondelete="CASCADE"), nullable=False)
    travel_date = Column(Date, nullable=False, index=True)
    status = Column(Enum(JourneyStatus), default=JourneyStatus.SCHEDULED, nullable=False)
    departure_datetime = Column(DateTime, nullable=False)
    arrival_datetime = Column(DateTime, nullable=False)

    train = relationship("Train", back_populates="journeys")
    inventories = relationship("JourneyInventory", back_populates="journey", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="journey")

    __table_args__ = (
        UniqueConstraint("train_id", "travel_date", name="uq_train_journey_date"),
        Index("ix_journey_search", "train_id", "travel_date"),
    )


class JourneyInventory(Base):
    __tablename__ = "journey_inventory"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("train_journeys.id", ondelete="CASCADE"), nullable=False)
    travel_class = Column(Enum(TravelClass), nullable=False)
    capacity = Column(Integer, default=10, nullable=False)
    available_seats = Column(Integer, default=10, nullable=False)
    waitlist_limit = Column(Integer, default=2, nullable=False)
    waitlist_count = Column(Integer, default=0, nullable=False)
    fare = Column(Numeric(10, 2), nullable=False)
    version = Column(Integer, default=1, nullable=False)

    journey = relationship("TrainJourney", back_populates="inventories")

    __table_args__ = (
        UniqueConstraint("journey_id", "travel_class", name="uq_journey_inventory_class"),
        Index("ix_inventory_lookup", "journey_id", "travel_class"),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String(14), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    journey_id = Column(Integer, ForeignKey("train_journeys.id"), nullable=False)
    travel_class = Column(Enum(TravelClass), nullable=False)
    passenger_count = Column(Integer, default=1, nullable=False)
    total_fare = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(TicketStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    cancelled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tickets")
    journey = relationship("TrainJourney", back_populates="tickets")
    passengers = relationship("Passenger", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ticket_user", "user_id", "created_at"),
    )


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    seat_number = Column(String(10), nullable=True)  # e.g., 'AC-1', 'GEN-4', or NULL if WL
    reservation_status = Column(Enum(ReservationStatus), nullable=False)  # CNF, WL, CAN
    waitlist_position = Column(Integer, nullable=True)

    ticket = relationship("Ticket", back_populates="passengers")

    __table_args__ = (
        Index("ix_passenger_ticket", "ticket_id"),
    )


class BookingEvent(Base):
    """
    Transactional Outbox Table.
    Every seat mutation atomically writes an outbox event in the same MySQL transaction.
    The worker picks up unprocessed rows and projects to Firebase and Azure Cosmos DB.
    """
    __tablename__ = "booking_events"

    id = Column(Integer, primary_key=True, index=True)
    aggregate_id = Column(String(50), nullable=False, index=True)  # PNR or Journey ID
    event_type = Column(String(50), nullable=False, index=True)    # e.g. 'BOOKING_CONFIRMED', 'BOOKING_CANCELLED'
    payload = Column(JSON, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    firebase_synced = Column(Boolean, default=False, nullable=False, index=True)
    cosmos_synced = Column(Boolean, default=False, nullable=False, index=True)
    firebase_error = Column(Text, nullable=True)
    cosmos_error = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    processed_at = Column(DateTime, nullable=True)


class SyntheticTrainStatus(Base):
    """
    Simulated operational status (delays, platform announcements)
    Managed via admin console and broadcasted to Firebase live projections.
    """
    __tablename__ = "synthetic_train_status"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    platform = Column(String(10), default="1", nullable=False)
    delay_minutes = Column(Integer, default=0, nullable=False)
    status_text = Column(String(50), default="ON TIME", nullable=False)  # ON TIME, DELAYED, CANCELLED
    announcement = Column(String(255), default="Train running on schedule", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    train = relationship("Train")
    current_station = relationship("Station")
