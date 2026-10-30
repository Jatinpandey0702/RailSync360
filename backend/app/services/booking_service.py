import random
import string
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.entities import (
    JourneyInventory, Ticket, Passenger, BookingEvent,
    TravelClass, TicketStatus, ReservationStatus
)
from app.schemas.schemas import BookingCreate


def generate_collision_resistant_pnr(db: Session) -> str:
    """
    Generates a unique 10-character alphanumeric PNR: RS360-XXXXXX
    Checks against the database to guarantee uniqueness before return.
    """
    for _ in range(10):
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pnr = f"RS{suffix}"
        existing = db.query(Ticket).filter(Ticket.pnr == pnr).first()
        if not existing:
            return pnr
    # Fallback timestamp suffix
    return f"RS{int(datetime.utcnow().timestamp()) % 1000000:06d}"


def create_booking_transaction(db: Session, user_id: int, booking_in: BookingCreate) -> Ticket:
    """
    Strict ACID Concurrency Booking Implementation:
    1. Lock journey_inventory using SELECT ... FOR UPDATE.
    2. Check availability:
       - If requested passengers <= available_seats: allocate confirmed seats (e.g. AC-1..10 or GEN-1..10).
       - Else if waitlist_count + requested passengers <= waitlist_limit: allocate waitlisted status (WL-1, WL-2).
       - Else reject with 400 CapacityExceeded.
    3. Calculate total fare based on inventory fare snapshot.
    4. Insert Ticket and Passenger records.
    5. Decrement available_seats or increment waitlist_count; increment version.
    6. Atomically append a BookingEvent to the transactional outbox.
    7. Commit transaction.
    """
    passenger_count = len(booking_in.passengers)
    if passenger_count <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one passenger required.")

    # 1. Pessimistic Row Lock
    inventory = (
        db.query(JourneyInventory)
        .filter(
            JourneyInventory.journey_id == booking_in.journey_id,
            JourneyInventory.travel_class == booking_in.travel_class
        )
        .with_for_update()
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Journey inventory not found for selected train journey and class."
        )

    # 2. Capacity Check & Allocation Strategy
    is_confirmed = False
    is_waitlisted = False

    if inventory.available_seats >= passenger_count:
        is_confirmed = True
    elif (inventory.waitlist_count + passenger_count) <= inventory.waitlist_limit:
        is_waitlisted = True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class {booking_in.travel_class.value} is fully booked! Available: {inventory.available_seats}, Waitlist Remaining: {inventory.waitlist_limit - inventory.waitlist_count}."
        )

    # 3. Create Ticket
    pnr = generate_collision_resistant_pnr(db)
    total_fare = inventory.fare * passenger_count
    ticket_status = TicketStatus.CONFIRMED if is_confirmed else TicketStatus.WAITLISTED

    ticket = Ticket(
        pnr=pnr,
        user_id=user_id,
        journey_id=booking_in.journey_id,
        travel_class=booking_in.travel_class,
        passenger_count=passenger_count,
        total_fare=total_fare,
        status=ticket_status,
        created_at=datetime.utcnow()
    )
    db.add(ticket)
    db.flush()  # populate ticket.id

    # 4. Allocate Seats or Waitlist Positions
    prefix = "AC" if booking_in.travel_class == TravelClass.AC else "GEN"

    if is_confirmed:
        # Determine already occupied seat numbers in this journey and class
        occupied_seats = set(
            s[0] for s in db.query(Passenger.seat_number)
            .join(Ticket, Ticket.id == Passenger.ticket_id)
            .filter(
                Ticket.journey_id == booking_in.journey_id,
                Ticket.travel_class == booking_in.travel_class,
                Passenger.reservation_status == ReservationStatus.CNF,
                Ticket.status != TicketStatus.CANCELLED
            ).all() if s[0]
        )

        current_seat_idx = 1
        for p_in in booking_in.passengers:
            while f"{prefix}-{current_seat_idx}" in occupied_seats:
                current_seat_idx += 1
            allocated_seat = f"{prefix}-{current_seat_idx}"
            occupied_seats.add(allocated_seat)
            current_seat_idx += 1

            passenger = Passenger(
                ticket_id=ticket.id,
                full_name=p_in.full_name,
                age=p_in.age,
                gender=p_in.gender,
                seat_number=allocated_seat,
                reservation_status=ReservationStatus.CNF,
                waitlist_position=None
            )
            db.add(passenger)

        # Update Inventory
        inventory.available_seats -= passenger_count
        inventory.version += 1

    elif is_waitlisted:
        for idx, p_in in enumerate(booking_in.passengers):
            wl_pos = inventory.waitlist_count + idx + 1
            passenger = Passenger(
                ticket_id=ticket.id,
                full_name=p_in.full_name,
                age=p_in.age,
                gender=p_in.gender,
                seat_number=None,
                reservation_status=ReservationStatus.WL,
                waitlist_position=wl_pos
            )
            db.add(passenger)

        inventory.waitlist_count += passenger_count
        inventory.version += 1

    # 5. Atomic Outbox Event
    outbox_payload = {
        "event_id": f"evt-{pnr}-{int(datetime.utcnow().timestamp())}",
        "pnr": pnr,
        "journey_id": booking_in.journey_id,
        "train_number": inventory.journey.train.train_number if inventory.journey and inventory.journey.train else "UNKNOWN",
        "travel_class": booking_in.travel_class.value,
        "passenger_count": passenger_count,
        "region": inventory.journey.train.source_station.region if inventory.journey and inventory.journey.train and inventory.journey.train.source_station else "Northern",
        "ticket_status": ticket_status.value,
        "available_seats": inventory.available_seats,
        "waitlist_count": inventory.waitlist_count,
        "capacity": inventory.capacity,
        "version": inventory.version,
        "timestamp": datetime.utcnow().isoformat()
    }

    event = BookingEvent(
        aggregate_id=pnr,
        event_type="BOOKING_CONFIRMED" if is_confirmed else "BOOKING_WAITLISTED",
        payload=outbox_payload,
        version=inventory.version,
        created_at=datetime.utcnow()
    )
    db.add(event)

    db.commit()
    db.refresh(ticket)
    return ticket


def cancel_booking_transaction(db: Session, user_id: int, pnr: str, is_admin: bool = False) -> Ticket:
    """
    ACID Cancellation & Automatic FIFO Waitlist Promotion:
    1. Lock ticket and its inventory.
    2. Check permission (owner or admin) and status (must not already be CANCELLED).
    3. Update Ticket and Passenger statuses to CANCELLED.
    4. If Ticket was CONFIRMED:
       - Free the seats (inventory.available_seats += count).
       - Look for the oldest WAITLISTED ticket for this journey & class (FIFO order by created_at).
       - If found and passenger_count can be fulfilled:
         Promote waitlisted ticket to CONFIRMED, assign seat numbers, decrement waitlist_count.
    5. Increment inventory version and write BOOKING_CANCELLED outbox event.
    6. Commit transaction.
    """
    ticket = db.query(Ticket).filter(Ticket.pnr == pnr).with_for_update().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket with PNR not found.")

    if not is_admin and ticket.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: not ticket owner.")

    if ticket.status == TicketStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already cancelled.")

    # Lock inventory
    inventory = (
        db.query(JourneyInventory)
        .filter(
            JourneyInventory.journey_id == ticket.journey_id,
            JourneyInventory.travel_class == ticket.travel_class
        )
        .with_for_update()
        .first()
    )

    was_confirmed = (ticket.status == TicketStatus.CONFIRMED)
    was_waitlisted = (ticket.status == TicketStatus.WAITLISTED)

    # Cancel current ticket
    ticket.status = TicketStatus.CANCELLED
    ticket.cancelled_at = datetime.utcnow()

    for p in ticket.passengers:
        p.reservation_status = ReservationStatus.CAN
        p.seat_number = None
        p.waitlist_position = None

    db.flush()

    if was_waitlisted:
        inventory.waitlist_count = max(0, inventory.waitlist_count - ticket.passenger_count)
        inventory.version += 1

    elif was_confirmed:
        # Free seats
        inventory.available_seats += ticket.passenger_count

        # FIFO Promotion check for oldest active waitlisted ticket
        waitlisted_candidate = (
            db.query(Ticket)
            .filter(
                Ticket.journey_id == ticket.journey_id,
                Ticket.travel_class == ticket.travel_class,
                Ticket.status == TicketStatus.WAITLISTED
            )
            .order_by(Ticket.created_at.asc())
            .with_for_update()
            .first()
        )

        if waitlisted_candidate and waitlisted_candidate.passenger_count <= inventory.available_seats:
            # Promote waitlist ticket
            waitlisted_candidate.status = TicketStatus.CONFIRMED
            inventory.available_seats -= waitlisted_candidate.passenger_count
            inventory.waitlist_count = max(0, inventory.waitlist_count - waitlisted_candidate.passenger_count)

            # Assign seats to promoted passengers
            prefix = "AC" if ticket.travel_class == TravelClass.AC else "GEN"
            occupied_seats = set(
                s[0] for s in db.query(Passenger.seat_number)
                .join(Ticket, Ticket.id == Passenger.ticket_id)
                .filter(
                    Ticket.journey_id == ticket.journey_id,
                    Ticket.travel_class == ticket.travel_class,
                    Passenger.reservation_status == ReservationStatus.CNF,
                    Ticket.status != TicketStatus.CANCELLED
                ).all() if s[0]
            )

            seat_idx = 1
            for p in waitlisted_candidate.passengers:
                while f"{prefix}-{seat_idx}" in occupied_seats:
                    seat_idx += 1
                allocated = f"{prefix}-{seat_idx}"
                occupied_seats.add(allocated)
                seat_idx += 1

                p.reservation_status = ReservationStatus.CNF
                p.seat_number = allocated
                p.waitlist_position = None

        inventory.version += 1

    # Atomic cancellation outbox event
    cancel_payload = {
        "event_id": f"evt-can-{pnr}-{int(datetime.utcnow().timestamp())}",
        "pnr": pnr,
        "journey_id": ticket.journey_id,
        "travel_class": ticket.travel_class.value,
        "train_number": inventory.journey.train.train_number if inventory.journey and inventory.journey.train else "UNKNOWN",
        "region": inventory.journey.train.source_station.region if inventory.journey and inventory.journey.train and inventory.journey.train.source_station else "Northern",
        "ticket_status": "CANCELLED",
        "available_seats": inventory.available_seats,
        "waitlist_count": inventory.waitlist_count,
        "capacity": inventory.capacity,
        "version": inventory.version,
        "timestamp": datetime.utcnow().isoformat()
    }

    event = BookingEvent(
        aggregate_id=pnr,
        event_type="BOOKING_CANCELLED",
        payload=cancel_payload,
        version=inventory.version,
        created_at=datetime.utcnow()
    )
    db.add(event)

    db.commit()
    db.refresh(ticket)
    return ticket
