from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.entities import (
    User, UserRole, Station, Train, TrainStop, TrainJourney,
    JourneyInventory, Ticket, SyntheticTrainStatus, BookingEvent, TravelClass, JourneyStatus
)
from app.schemas.schemas import (
    UserRegister, UserLogin, Token, UserOut,
    StationOut, TrainDetailOut, TrainStopOut, JourneySearchItem, ClassAvailabilityOut,
    BookingCreate, TicketOut, LiveTrainStatusOut, AdminStatusUpdate, SyncHealthOut, OutboxEventOut
)
from app.services.booking_service import create_booking_transaction, cancel_booking_transaction
from app.integrations.cloud_adapters import CloudIntegrationManager

router = APIRouter()


# --- Dependencies ---
def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    # Standard header extraction
    pass

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privilege required.")
    return current_user


# ==========================================
# 1. AUTHENTICATION ENDPOINTS
# ==========================================
@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_pw,
        role=user_in.role or UserRole.PASSENGER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(data={"sub": user.email, "role": user.role.value, "name": user.name})
    return Token(
        access_token=token,
        role=user.role,
        name=user.name,
        email=user.email
    )


@router.get("/auth/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# ==========================================
# 2. STATIONS & TRAIN CATALOG
# ==========================================
@router.get("/stations", response_model=List[StationOut])
def get_stations(db: Session = Depends(get_db)):
    return db.query(Station).order_by(Station.name.asc()).all()


@router.get("/trains", response_model=List[TrainDetailOut])
def get_trains(db: Session = Depends(get_db)):
    trains = db.query(Train).filter(Train.active == True).all()
    results = []
    for t in trains:
        stops_out = [
            TrainStopOut(
                stop_sequence=s.stop_sequence,
                station_id=s.station_id,
                station_code=s.station.station_code,
                station_name=s.station.name,
                region=s.station.region,
                arrival_time=s.arrival_time,
                departure_time=s.departure_time,
                distance_km=s.distance_km
            ) for s in t.stops
        ]
        results.append(TrainDetailOut(
            id=t.id,
            train_number=t.train_number,
            train_name=t.train_name,
            source_station=t.source_station,
            destination_station=t.destination_station,
            active=t.active,
            stops=stops_out
        ))
    return results


@router.get("/trains/{train_id}", response_model=TrainDetailOut)
def get_train_by_id(train_id: int, db: Session = Depends(get_db)):
    t = db.query(Train).filter(Train.id == train_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Train not found.")
    stops_out = [
        TrainStopOut(
            stop_sequence=s.stop_sequence,
            station_id=s.station_id,
            station_code=s.station.station_code,
            station_name=s.station.name,
            region=s.station.region,
            arrival_time=s.arrival_time,
            departure_time=s.departure_time,
            distance_km=s.distance_km
        ) for s in t.stops
    ]
    return TrainDetailOut(
        id=t.id,
        train_number=t.train_number,
        train_name=t.train_name,
        source_station=t.source_station,
        destination_station=t.destination_station,
        active=t.active,
        stops=stops_out
    )


# ==========================================
# 3. JOURNEY SEARCH & SEAT AVAILABILITY
# ==========================================
@router.get("/journeys/search", response_model=List[JourneySearchItem])
def search_journeys(
    source: Optional[str] = Query(None, description="Source Station Code or ID"),
    destination: Optional[str] = Query(None, description="Destination Station Code or ID"),
    travel_date: Optional[str] = Query(None, description="YYYY-MM-DD within next 7 days"),
    db: Session = Depends(get_db)
):
    query = db.query(TrainJourney).join(Train, Train.id == TrainJourney.train_id)

    if travel_date:
        try:
            parsed_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
            query = query.filter(TrainJourney.travel_date == parsed_date)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    if source and destination:
        from sqlalchemy.orm import aliased
        StopSource = aliased(TrainStop)
        StopDest = aliased(TrainStop)
        StationSource = aliased(Station)
        StationDest = aliased(Station)

        query = (
            query
            .join(StopSource, StopSource.train_id == Train.id)
            .join(StationSource, StationSource.id == StopSource.station_id)
            .join(StopDest, StopDest.train_id == Train.id)
            .join(StationDest, StationDest.id == StopDest.station_id)
            .filter(
                StopSource.stop_sequence < StopDest.stop_sequence,
                or_(StationSource.station_code == source.upper(), StationSource.name.ilike(f"%{source}%")),
                or_(StationDest.station_code == destination.upper(), StationDest.name.ilike(f"%{destination}%"))
            )
        )
    elif source:
        from sqlalchemy.orm import aliased
        StopSource = aliased(TrainStop)
        StationSource = aliased(Station)
        query = (
            query
            .join(StopSource, StopSource.train_id == Train.id)
            .join(StationSource, StationSource.id == StopSource.station_id)
            .filter(or_(StationSource.station_code == source.upper(), StationSource.name.ilike(f"%{source}%")))
        )
    elif destination:
        from sqlalchemy.orm import aliased
        StopDest = aliased(TrainStop)
        StationDest = aliased(Station)
        query = (
            query
            .join(StopDest, StopDest.train_id == Train.id)
            .join(StationDest, StationDest.id == StopDest.station_id)
            .filter(or_(StationDest.station_code == destination.upper(), StationDest.name.ilike(f"%{destination}%")))
        )

    journeys = query.order_by(TrainJourney.departure_datetime.asc()).all()

    items = []
    for j in journeys:
        availabilities = [
            ClassAvailabilityOut(
                travel_class=inv.travel_class,
                capacity=inv.capacity,
                available_seats=inv.available_seats,
                waitlist_limit=inv.waitlist_limit,
                waitlist_count=inv.waitlist_count,
                fare=inv.fare,
                version=inv.version
            ) for inv in j.inventories
        ]

        items.append(JourneySearchItem(
            journey_id=j.id,
            train_id=j.train.id,
            train_number=j.train.train_number,
            train_name=j.train.train_name,
            source_station=j.train.source_station,
            destination_station=j.train.destination_station,
            travel_date=j.travel_date,
            departure_datetime=j.departure_datetime,
            arrival_datetime=j.arrival_datetime,
            status=j.status,
            availability=availabilities
        ))
    return items


@router.get("/journeys/{journey_id}/availability", response_model=List[ClassAvailabilityOut])
def get_journey_availability(journey_id: int, db: Session = Depends(get_db)):
    inventories = db.query(JourneyInventory).filter(JourneyInventory.journey_id == journey_id).all()
    if not inventories:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found.")
    return [
        ClassAvailabilityOut(
            travel_class=inv.travel_class,
            capacity=inv.capacity,
            available_seats=inv.available_seats,
            waitlist_limit=inv.waitlist_limit,
            waitlist_count=inv.waitlist_count,
            fare=inv.fare,
            version=inv.version
        ) for inv in inventories
    ]


# ==========================================
# 4. BOOKING TRANSACTIONS & PNR MANAGEMENT
# ==========================================
@router.post("/bookings", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ticket = create_booking_transaction(db, user_id=current_user.id, booking_in=booking_in)
    return format_ticket_out(ticket)


@router.get("/bookings/me", response_model=List[TicketOut])
def get_my_bookings(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return [format_ticket_out(t) for t in tickets]


@router.get("/bookings/{pnr}", response_model=TicketOut)
def get_booking_by_pnr(
    pnr: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.pnr == pnr.upper()).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PNR record not found.")

    if current_user.role != UserRole.ADMIN and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return format_ticket_out(ticket)


@router.post("/bookings/{pnr}/cancel", response_model=TicketOut)
def cancel_booking(
    pnr: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    is_admin = (current_user.role == UserRole.ADMIN)
    ticket = cancel_booking_transaction(db, user_id=current_user.id, pnr=pnr.upper(), is_admin=is_admin)
    return format_ticket_out(ticket)


def format_ticket_out(ticket: Ticket) -> TicketOut:
    return TicketOut(
        id=ticket.id,
        pnr=ticket.pnr,
        user_id=ticket.user_id,
        journey_id=ticket.journey_id,
        train_number=ticket.journey.train.train_number if ticket.journey else "UNKNOWN",
        train_name=ticket.journey.train.train_name if ticket.journey else "UNKNOWN",
        source_station_code=ticket.journey.train.source_station.station_code if ticket.journey else "",
        destination_station_code=ticket.journey.train.destination_station.station_code if ticket.journey else "",
        travel_date=ticket.journey.travel_date if ticket.journey else datetime.utcnow().date(),
        travel_class=ticket.travel_class,
        passenger_count=ticket.passenger_count,
        total_fare=ticket.total_fare,
        status=ticket.status,
        created_at=ticket.created_at,
        cancelled_at=ticket.cancelled_at,
        passengers=ticket.passengers
    )


# ==========================================
# 5. LIVE RUNNING STATUS & ANNOUNCEMENTS
# ==========================================
@router.get("/live/trains/{train_id}", response_model=LiveTrainStatusOut)
def get_live_train_status(train_id: int, db: Session = Depends(get_db)):
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Train not found.")

    status_obj = db.query(SyntheticTrainStatus).filter(SyntheticTrainStatus.train_id == train_id).first()
    if not status_obj:
        return LiveTrainStatusOut(
            train_id=train.id,
            train_number=train.train_number,
            train_name=train.train_name,
            platform="1",
            delay_minutes=0,
            status_text="ON TIME",
            announcement="Train running on schedule",
            updated_at=datetime.utcnow(),
            is_simulated=True
        )

    return LiveTrainStatusOut(
        train_id=train.id,
        train_number=train.train_number,
        train_name=train.train_name,
        platform=status_obj.platform,
        delay_minutes=status_obj.delay_minutes,
        status_text=status_obj.status_text,
        announcement=status_obj.announcement,
        updated_at=status_obj.updated_at,
        is_simulated=True
    )


@router.put("/admin/trains/{train_id}/status", response_model=LiveTrainStatusOut)
def update_train_status_simulation(
    train_id: int,
    status_in: AdminStatusUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Train not found.")

    status_obj = db.query(SyntheticTrainStatus).filter(SyntheticTrainStatus.train_id == train_id).first()
    if not status_obj:
        status_obj = SyntheticTrainStatus(train_id=train_id)
        db.add(status_obj)

    if status_in.platform is not None:
        status_obj.platform = status_in.platform
    if status_in.delay_minutes is not None:
        status_obj.delay_minutes = status_in.delay_minutes
    if status_in.status_text is not None:
        status_obj.status_text = status_in.status_text
    if status_in.announcement is not None:
        status_obj.announcement = status_in.announcement
    status_obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(status_obj)

    return LiveTrainStatusOut(
        train_id=train.id,
        train_number=train.train_number,
        train_name=train.train_name,
        platform=status_obj.platform,
        delay_minutes=status_obj.delay_minutes,
        status_text=status_obj.status_text,
        announcement=status_obj.announcement,
        updated_at=status_obj.updated_at,
        is_simulated=True
    )


# ==========================================
# 6. ADMIN METRICS & CLOUD DIAGNOSTICS
# ==========================================
@router.get("/analytics/booking-trends")
def get_public_booking_trends(db: Session = Depends(get_db)):
    """
    Publicly accessible endpoint for all passengers and visitors to inspect
    booking trends, historical demand, and regional distribution.
    """
    total_tickets = db.query(Ticket).count()
    confirmed_tickets = db.query(Ticket).filter(Ticket.status == "CONFIRMED").count()
    waitlisted_tickets = db.query(Ticket).filter(Ticket.status == "WAITLISTED").count()
    cancelled_tickets = db.query(Ticket).filter(Ticket.status == "CANCELLED").count()

    # Regional bookings summary
    regional_counts = {}
    events = db.query(BookingEvent).filter(BookingEvent.event_type.in_(["BOOKING_CONFIRMED", "BOOKING_WAITLISTED"])).all()
    for e in events:
        reg = (e.payload or {}).get("region", "Northern")
        regional_counts[reg] = regional_counts.get(reg, 0) + 1

    # Daily booking velocity & demand trends
    daily_trends = {}
    tickets = db.query(Ticket).order_by(Ticket.created_at.asc()).all()
    for t in tickets:
        d_str = t.created_at.strftime("%b %d")
        if d_str not in daily_trends:
            daily_trends[d_str] = {"date": d_str, "confirmed": 0, "cancelled": 0, "waitlisted": 0, "total": 0}
        daily_trends[d_str]["total"] += 1
        if t.status.value == "CONFIRMED":
            daily_trends[d_str]["confirmed"] += 1
        elif t.status.value == "CANCELLED":
            daily_trends[d_str]["cancelled"] += 1
        elif t.status.value == "WAITLISTED":
            daily_trends[d_str]["waitlisted"] += 1

    trends_list = list(daily_trends.values())
    if not trends_list:
        trends_list = [{"date": "Today", "confirmed": confirmed_tickets, "cancelled": cancelled_tickets, "waitlisted": waitlisted_tickets, "total": total_tickets}]

    # Popular route demand
    route_demand = [
        {"route": "NDLS → BCT (Rajdhani)", "demand": 94, "region": "Northern/Western"},
        {"route": "HWH → NDLS (Rajdhani)", "demand": 88, "region": "Eastern/Northern"},
        {"route": "NDLS → MAS (TN Express)", "demand": 76, "region": "Northern/Southern"},
        {"route": "SBC → NDLS (Rajdhani)", "demand": 82, "region": "Southern/Northern"},
        {"route": "BCT → NDLS (Tejas)", "demand": 91, "region": "Western/Northern"},
    ]

    ac_count = db.query(Ticket).filter(Ticket.travel_class == "AC").count()
    gen_count = db.query(Ticket).filter(Ticket.travel_class == "GENERAL").count()

    return {
        "total_tickets": total_tickets,
        "confirmed_tickets": confirmed_tickets,
        "waitlisted_tickets": waitlisted_tickets,
        "cancelled_tickets": cancelled_tickets,
        "regional_breakdown": regional_counts,
        "daily_trends": trends_list,
        "route_demand": route_demand,
        "class_breakdown": [
            {"name": "AC Tier", "value": ac_count},
            {"name": "General", "value": gen_count}
        ]
    }


@router.get("/admin/metrics")
def get_admin_metrics(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    trends = get_public_booking_trends(db)
    total_users = db.query(User).count()
    return {
        "total_users": total_users,
        **trends
    }


@router.get("/admin/sync-health", response_model=SyncHealthOut)
def get_sync_health(admin_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    fb_status = CloudIntegrationManager.get_firebase_status()
    cos_status = CloudIntegrationManager.get_cosmos_status()

    pending_events = db.query(BookingEvent).filter(
        (BookingEvent.firebase_synced == False) | (BookingEvent.cosmos_synced == False)
    ).count()

    failed_events = db.query(BookingEvent).filter(
        (BookingEvent.firebase_error.isnot(None)) | (BookingEvent.cosmos_error.isnot(None))
    ).count()

    total_synced = db.query(BookingEvent).filter(
        (BookingEvent.firebase_synced == True) & (BookingEvent.cosmos_synced == True)
    ).count()

    return SyncHealthOut(
        app_profile=settings.APP_PROFILE,
        mysql_connected=True,
        firebase_configured=CloudIntegrationManager.is_firebase_enabled(),
        firebase_status=fb_status["status"],
        cosmos_configured=CloudIntegrationManager.is_cosmos_enabled(),
        cosmos_status=cos_status["status"],
        pending_events_count=pending_events,
        failed_events_count=failed_events,
        total_events_synced=total_synced
    )


@router.get("/admin/outbox-events", response_model=List[OutboxEventOut])
def get_outbox_events(
    limit: int = 50,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    events = db.query(BookingEvent).order_by(BookingEvent.id.desc()).limit(limit).all()
    return events


@router.post("/admin/sync/retry/{event_id}")
def retry_sync_event(
    event_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    event = db.query(BookingEvent).filter(BookingEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outbox event not found.")

    payload = event.payload or {}
    fb_success, fb_msg = CloudIntegrationManager.publish_seat_projection_to_firebase(
        payload.get("journey_id"), payload.get("travel_class"), payload
    )
    cos_success, cos_msg = CloudIntegrationManager.publish_regional_event_to_cosmos(payload)

    event.firebase_synced = fb_success
    event.firebase_error = None if fb_success else fb_msg
    event.cosmos_synced = cos_success
    event.cosmos_error = None if cos_success else cos_msg
    event.attempts += 1
    if fb_success and cos_success:
        event.processed_at = datetime.utcnow()

    db.commit()
    return {"message": "Sync retry dispatched", "firebase_synced": fb_success, "cosmos_synced": cos_success}
