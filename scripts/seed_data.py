import os
import sys
from datetime import datetime, date, time, timedelta
from decimal import Decimal

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Station, Train, TrainStop, TrainJourney,
    JourneyInventory, TravelClass, SyntheticTrainStatus
)


def seed_database():
    print("=" * 60)
    print("RailSync 360: Initializing Relational Tables and Seed Data...")
    print("=" * 60)

    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users (Admin & Passenger)
        if not db.query(User).filter(User.email == "admin@railsync360.internal").first():
            admin_user = User(
                name="Chief Traffic Controller",
                email="admin@railsync360.internal",
                password_hash=get_password_hash("AdminPass2026!"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            print("  [+] Created Admin User: admin@railsync360.internal / AdminPass2026!")

        if not db.query(User).filter(User.email == "passenger@example.com").first():
            demo_user = User(
                name="Aarav Sharma",
                email="passenger@example.com",
                password_hash=get_password_hash("Passenger123!"),
                role=UserRole.PASSENGER
            )
            db.add(demo_user)
            print("  [+] Created Passenger User: passenger@example.com / Passenger123!")

        db.commit()

        # 2. Seed Stations (Major Indian Railway Hubs across regions)
        stations_data = [
            {"code": "NDLS", "name": "New Delhi", "region": "Northern"},
            {"code": "BCT", "name": "Mumbai Central", "region": "Western"},
            {"code": "HWH", "name": "Howrah Junction (Kolkata)", "region": "Eastern"},
            {"code": "MAS", "name": "Chennai Central", "region": "Southern"},
            {"code": "SBC", "name": "KSR Bengaluru", "region": "South Western"},
            {"code": "CNB", "name": "Kanpur Central", "region": "Northern"},
            {"code": "BBR", "name": "Vadodara Junction", "region": "Western"},
        ]

        station_map = {}
        for s in stations_data:
            existing = db.query(Station).filter(Station.station_code == s["code"]).first()
            if not existing:
                station = Station(station_code=s["code"], name=s["name"], region=s["region"])
                db.add(station)
                db.flush()
                station_map[s["code"]] = station
                print(f"  [+] Station created: {s['code']} - {s['name']} ({s['region']})")
            else:
                station_map[s["code"]] = existing

        db.commit()

        # 3. Seed 5 Illustrative Demonstration Trains
        trains_data = [
            {
                "number": "12952",
                "name": "New Delhi - Mumbai Central Rajdhani Express",
                "source": "NDLS",
                "dest": "BCT",
                "stops": [
                    {"code": "NDLS", "seq": 1, "arr": None, "dep": time(16, 55), "dist": 0},
                    {"code": "CNB", "seq": 2, "arr": time(21, 30), "dep": time(21, 35), "dist": 440},
                    {"code": "BBR", "seq": 3, "arr": time(4, 30), "dep": time(4, 38), "dist": 992},
                    {"code": "BCT", "seq": 4, "arr": time(8, 35), "dep": None, "dist": 1384},
                ],
                "ac_fare": Decimal("2450.00"),
                "gen_fare": Decimal("620.00"),
                "dep_hour": 16,
                "dep_min": 55,
                "duration_hours": 15,
                "duration_mins": 40
            },
            {
                "number": "12301",
                "name": "Howrah - New Delhi Rajdhani Express",
                "source": "HWH",
                "dest": "NDLS",
                "stops": [
                    {"code": "HWH", "seq": 1, "arr": None, "dep": time(16, 50), "dist": 0},
                    {"code": "CNB", "seq": 2, "arr": time(4, 40), "dep": time(4, 45), "dist": 1010},
                    {"code": "NDLS", "seq": 3, "arr": time(10, 5), "dep": None, "dist": 1450},
                ],
                "ac_fare": Decimal("2350.00"),
                "gen_fare": Decimal("590.00"),
                "dep_hour": 16,
                "dep_min": 50,
                "duration_hours": 17,
                "duration_mins": 15
            },
            {
                "number": "12622",
                "name": "New Delhi - Chennai Central Tamil Nadu Express",
                "source": "NDLS",
                "dest": "MAS",
                "stops": [
                    {"code": "NDLS", "seq": 1, "arr": None, "dep": time(21, 5), "dist": 0},
                    {"code": "CNB", "seq": 2, "arr": time(2, 50), "dep": time(2, 55), "dist": 440},
                    {"code": "MAS", "seq": 3, "arr": time(6, 15), "dep": None, "dist": 2184},
                ],
                "ac_fare": Decimal("2850.00"),
                "gen_fare": Decimal("750.00"),
                "dep_hour": 21,
                "dep_min": 5,
                "duration_hours": 33,
                "duration_mins": 10
            },
            {
                "number": "22692",
                "name": "KSR Bengaluru - New Delhi Rajdhani Express",
                "source": "SBC",
                "dest": "NDLS",
                "stops": [
                    {"code": "SBC", "seq": 1, "arr": None, "dep": time(20, 0), "dist": 0},
                    {"code": "CNB", "seq": 2, "arr": time(0, 30), "dep": time(0, 35), "dist": 1920},
                    {"code": "NDLS", "seq": 3, "arr": time(5, 55), "dep": None, "dist": 2360},
                ],
                "ac_fare": Decimal("3100.00"),
                "gen_fare": Decimal("810.00"),
                "dep_hour": 20,
                "dep_min": 0,
                "duration_hours": 33,
                "duration_mins": 55
            },
            {
                "number": "12951",
                "name": "Mumbai Central - New Delhi Tejas Rajdhani",
                "source": "BCT",
                "dest": "NDLS",
                "stops": [
                    {"code": "BCT", "seq": 1, "arr": None, "dep": time(17, 0), "dist": 0},
                    {"code": "BBR", "seq": 2, "arr": time(21, 0), "dep": time(21, 5), "dist": 392},
                    {"code": "CNB", "seq": 3, "arr": time(4, 0), "dep": time(4, 5), "dist": 944},
                    {"code": "NDLS", "seq": 4, "arr": time(8, 32), "dep": None, "dist": 1384},
                ],
                "ac_fare": Decimal("2550.00"),
                "gen_fare": Decimal("640.00"),
                "dep_hour": 17,
                "dep_min": 0,
                "duration_hours": 15,
                "duration_mins": 32
            }
        ]

        created_trains = []
        for td in trains_data:
            train = db.query(Train).filter(Train.train_number == td["number"]).first()
            if not train:
                train = Train(
                    train_number=td["number"],
                    train_name=td["name"],
                    source_station_id=station_map[td["source"]].id,
                    destination_station_id=station_map[td["dest"]].id,
                    active=True
                )
                db.add(train)
                db.flush()

                # Add stops
                for s in td["stops"]:
                    stop = TrainStop(
                        train_id=train.id,
                        station_id=station_map[s["code"]].id,
                        stop_sequence=s["seq"],
                        arrival_time=s["arr"],
                        departure_time=s["dep"],
                        distance_km=s["dist"]
                    )
                    db.add(stop)

                # Add initial simulated status
                synth = SyntheticTrainStatus(
                    train_id=train.id,
                    platform="1",
                    delay_minutes=0,
                    status_text="ON TIME",
                    announcement="Train running on schedule"
                )
                db.add(synth)
                print(f"  [+] Train created: {td['number']} - {td['name']}")
            created_trains.append((train, td))

        db.commit()

        # 4. Seed Train Journeys for the next 7 days with AC and General Inventory
        today = date.today()
        for train, td in created_trains:
            for day_offset in range(7):
                travel_date = today + timedelta(days=day_offset)
                existing_journey = db.query(TrainJourney).filter(
                    TrainJourney.train_id == train.id,
                    TrainJourney.travel_date == travel_date
                ).first()

                if not existing_journey:
                    dep_dt = datetime.combine(travel_date, time(td["dep_hour"], td["dep_min"]))
                    arr_dt = dep_dt + timedelta(hours=td["duration_hours"], minutes=td["duration_mins"])

                    journey = TrainJourney(
                        train_id=train.id,
                        travel_date=travel_date,
                        status="SCHEDULED",
                        departure_datetime=dep_dt,
                        arrival_datetime=arr_dt
                    )
                    db.add(journey)
                    db.flush()

                    # AC Class Inventory: 10 capacity, 10 available, 2 waitlist limit
                    inv_ac = JourneyInventory(
                        journey_id=journey.id,
                        travel_class=TravelClass.AC,
                        capacity=10,
                        available_seats=10,
                        waitlist_limit=2,
                        waitlist_count=0,
                        fare=td["ac_fare"],
                        version=1
                    )
                    # General Class Inventory: 10 capacity, 10 available, 2 waitlist limit
                    inv_gen = JourneyInventory(
                        journey_id=journey.id,
                        travel_class=TravelClass.GENERAL,
                        capacity=10,
                        available_seats=10,
                        waitlist_limit=2,
                        waitlist_count=0,
                        fare=td["gen_fare"],
                        version=1
                    )
                    db.add(inv_ac)
                    db.add(inv_gen)

        db.commit()
        print("  [+] Successfully seeded 7-day journey inventories (10 seats/2 waitlist per class)!")
        print("=" * 60)
        print("Database Seed Finished Successfully!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
