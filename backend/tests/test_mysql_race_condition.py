import pytest
import concurrent.futures
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.entities import (
    User, TrainJourney, JourneyInventory, TravelClass
)
from app.schemas.schemas import BookingCreate, PassengerInput
from app.services.booking_service import create_booking_transaction


def test_concurrent_simultaneous_bookings_on_last_seat():
    """
    CONCURRENCY RIGOR TEST:
    Simulate two concurrent threads attempting to book the LAST available seat simultaneously.
    Verifies that pessimistic locking (SELECT ... FOR UPDATE) in MySQL guarantees:
    - Exactly one thread succeeds in confirming the seat.
    - The other thread is rejected, never creating duplicate seat numbers or negative availability.
    """
    mysql_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)

    # 1. Setup in an isolated session
    with SessionFactory() as setup_db:
        user1 = setup_db.query(User).filter(User.email == "passenger@example.com").first()
        user2 = setup_db.query(User).filter(User.email == "admin@railsync360.internal").first()
        assert user1 and user2, "Seeded users required"

        user1_id = user1.id
        user2_id = user2.id

        journey = setup_db.query(TrainJourney).first()
        assert journey is not None, "Seed data must exist"
        journey_id = journey.id

        inv = setup_db.query(JourneyInventory).filter(
            JourneyInventory.journey_id == journey_id,
            JourneyInventory.travel_class == TravelClass.AC
        ).first()

        original_seats = inv.available_seats
        original_wl = inv.waitlist_limit

        inv.available_seats = 1
        inv.waitlist_limit = 0  # Zero waitlist to force race condition on the last seat
        setup_db.commit()

    # 2. Worker function with its own dedicated session
    def attempt_booking(u_id):
        with SessionFactory() as session:
            try:
                booking_in = BookingCreate(
                    journey_id=journey_id,
                    travel_class=TravelClass.AC,
                    passengers=[PassengerInput(full_name=f"Racer-{u_id}", age=25, gender="MALE")]
                )
                ticket = create_booking_transaction(session, user_id=u_id, booking_in=booking_in)
                return {"status": "SUCCESS", "pnr": ticket.pnr}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}

    # 3. Fire concurrent attempts
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_booking, user1_id)
        f2 = executor.submit(attempt_booking, user2_id)
        res1 = f1.result()
        res2 = f2.result()

    results = [res1["status"], res2["status"]]

    # 4. Assert invariants and restore state in fresh session
    with SessionFactory() as cleanup_db:
        inv_check = cleanup_db.query(JourneyInventory).filter(
            JourneyInventory.journey_id == journey_id,
            JourneyInventory.travel_class == TravelClass.AC
        ).first()

        # Invariant checks
        assert results.count("SUCCESS") == 1, f"Expected 1 SUCCESS, got {results}"
        assert results.count("FAILED") == 1, f"Expected 1 FAILED, got {results}"
        assert inv_check.available_seats == 0, f"Expected 0 remaining seats, got {inv_check.available_seats}"

        # Restore
        inv_check.available_seats = original_seats
        inv_check.waitlist_limit = original_wl
        cleanup_db.commit()
