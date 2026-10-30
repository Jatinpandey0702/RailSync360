import pytest
import concurrent.futures
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Station, Train, TrainStop, TrainJourney,
    JourneyInventory, Ticket, Passenger, BookingEvent, TravelClass, TicketStatus, ReservationStatus
)
from app.schemas.schemas import BookingCreate, PassengerInput
from app.services.booking_service import create_booking_transaction, cancel_booking_transaction

# Test Database Engine (In-Memory SQLite or local test DB)
# Note: SQLite supports transactions, but for strict row-level lock concurrency, MySQL is best.
# Here we test transaction semantics and promotion logic.
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Seed minimal test dataset
    u1 = User(name="User 1", email="user1@test.com", password_hash=get_password_hash("pass"), role=UserRole.PASSENGER)
    u2 = User(name="User 2", email="user2@test.com", password_hash=get_password_hash("pass"), role=UserRole.PASSENGER)
    u3 = User(name="User 3", email="user3@test.com", password_hash=get_password_hash("pass"), role=UserRole.PASSENGER)
    session.add_all([u1, u2, u3])
    session.flush()

    s1 = Station(station_code="NDLS", name="New Delhi", region="Northern")
    s2 = Station(station_code="BCT", name="Mumbai Central", region="Western")
    session.add_all([s1, s2])
    session.flush()

    t = Train(train_number="12952", train_name="Rajdhani", source_station_id=s1.id, destination_station_id=s2.id)
    session.add(t)
    session.flush()

    j = TrainJourney(
        train_id=t.id,
        travel_date=date.today() + timedelta(days=1),
        departure_datetime=datetime.utcnow() + timedelta(days=1),
        arrival_datetime=datetime.utcnow() + timedelta(days=1, hours=16)
    )
    session.add(j)
    session.flush()

    # Inventory with exactly 2 available seats and 2 waitlist limit
    inv_ac = JourneyInventory(
        journey_id=j.id,
        travel_class=TravelClass.AC,
        capacity=2,
        available_seats=2,
        waitlist_limit=2,
        waitlist_count=0,
        fare=Decimal("2000.00"),
        version=1
    )
    session.add(inv_ac)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


def test_booking_and_waitlist_and_fifo_promotion(db_session):
    """
    Test Complete Lifecycle:
    1. Book 2 seats -> Both CONFIRMED, inventory available = 0.
    2. Book 1 seat -> WAITLISTED (WL-1), inventory waitlist_count = 1.
    3. Book 1 seat -> WAITLISTED (WL-2), inventory waitlist_count = 2.
    4. Try booking 1 more seat -> Rejection (400 CapacityExceeded).
    5. Cancel 1st CONFIRMED ticket -> Automatically promotes WL-1 to CONFIRMED!
    6. Verify promoted ticket has seat allocated and inventory reconciled.
    """
    user1 = db_session.query(User).filter(User.email == "user1@test.com").first()
    user2 = db_session.query(User).filter(User.email == "user2@test.com").first()
    user3 = db_session.query(User).filter(User.email == "user3@test.com").first()
    journey = db_session.query(TrainJourney).first()

    # 1. Book first 2 seats (User 1)
    booking1 = BookingCreate(
        journey_id=journey.id,
        travel_class=TravelClass.AC,
        passengers=[
            PassengerInput(full_name="Passenger A", age=30, gender="MALE"),
            PassengerInput(full_name="Passenger B", age=28, gender="FEMALE")
        ]
    )
    t1 = create_booking_transaction(db_session, user1.id, booking1)
    assert t1.status == TicketStatus.CONFIRMED
    assert len(t1.passengers) == 2
    assert t1.passengers[0].reservation_status == ReservationStatus.CNF
    assert t1.passengers[0].seat_number == "AC-1"
    assert t1.passengers[1].seat_number == "AC-2"

    inv = db_session.query(JourneyInventory).filter(JourneyInventory.journey_id == journey.id).first()
    assert inv.available_seats == 0
    assert inv.waitlist_count == 0

    # 2. Book 3rd seat (User 2) -> Should become WL-1
    booking2 = BookingCreate(
        journey_id=journey.id,
        travel_class=TravelClass.AC,
        passengers=[PassengerInput(full_name="Passenger C", age=45, gender="MALE")]
    )
    t2 = create_booking_transaction(db_session, user2.id, booking2)
    assert t2.status == TicketStatus.WAITLISTED
    assert t2.passengers[0].reservation_status == ReservationStatus.WL
    assert t2.passengers[0].waitlist_position == 1

    db_session.refresh(inv)
    assert inv.available_seats == 0
    assert inv.waitlist_count == 1

    # 3. Book 4th seat (User 3) -> Should become WL-2
    booking3 = BookingCreate(
        journey_id=journey.id,
        travel_class=TravelClass.AC,
        passengers=[PassengerInput(full_name="Passenger D", age=22, gender="FEMALE")]
    )
    t3 = create_booking_transaction(db_session, user3.id, booking3)
    assert t3.status == TicketStatus.WAITLISTED
    assert t3.passengers[0].reservation_status == ReservationStatus.WL
    assert t3.passengers[0].waitlist_position == 2

    db_session.refresh(inv)
    assert inv.available_seats == 0
    assert inv.waitlist_count == 2

    # 4. Attempt 5th seat -> Capacity Exceeded
    with pytest.raises(Exception) as exc_info:
        create_booking_transaction(db_session, user1.id, booking3)
    assert "fully booked" in str(exc_info.value.detail).lower()

    # 5. Cancel Ticket 1 (which had 2 confirmed seats)
    cancel_booking_transaction(db_session, user1.id, t1.pnr)
    db_session.refresh(t1)
    assert t1.status == TicketStatus.CANCELLED

    # 6. Check FIFO Promotion: Ticket 2 (User 2) should now be CONFIRMED with seat AC-1!
    db_session.refresh(t2)
    for p in t2.passengers:
        db_session.refresh(p)
    assert t2.status == TicketStatus.CONFIRMED
    assert t2.passengers[0].reservation_status == ReservationStatus.CNF
    assert t2.passengers[0].seat_number == "AC-1"

    # Inventory reconciliation check
    db_session.refresh(inv)
    # Freed 2 seats, 1 promoted -> 1 available seat remaining, 1 waitlisted remaining
    assert inv.available_seats == 1
    assert inv.waitlist_count == 1
