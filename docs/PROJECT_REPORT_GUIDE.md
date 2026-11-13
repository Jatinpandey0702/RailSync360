# RailSync 360 — Complete Engineering Project Documentation & Report Guide

> **Project Name:** RailSync 360 — Cloud Railway Reservation & Distributed Records System  
> **Course / Context:** Advanced Database Management Systems (ADBMS) / Cloud Data Architecture  
> **Repository:** [https://github.com/Jatinpandey0702/RailSync360](https://github.com/Jatinpandey0702/RailSync360)  
> **Tech Stack:** Python 3.12 (FastAPI, SQLAlchemy 2, Alembic, Pydantic v2), React 19 (TypeScript, Vite, Tailwind CSS, TanStack Query), MySQL 8 (ACID Core), Firebase Realtime DB (Live Push), Azure Cosmos DB (Regional Records).

---

## 1. Project Overview & Problem Statement

### 1.1 Problem Statement
Railway ticketing and inventory systems require ultra-reliable concurrency control, immediate consistency during bookings, and sub-second updates for live seat availability across thousands of distributed clients. Relying on a single monolithic database architecture creates severe bottlenecks:
- Relational databases ensure strict ACID compliance but suffer query degradation when thousands of clients continuously poll for live seat counts.
- Pure NoSQL document stores offer horizontal scale and flexible partitioning but cannot easily guarantee strict pessimistic row locking or zero-overbooking guarantees without complex application-level lock orchestration.

### 1.2 The RailSync 360 Solution
RailSync 360 solves this trade-off using a **Polyglot Multi-Database Architecture** coupled with the **Transactional Outbox Pattern**:
1. **Authoritative ACID Core (MySQL 8):** Normalized to 3rd Normal Form (3NF). Every reservation and seat allocation executes with pessimistic row-level locking (`SELECT ... FOR UPDATE`), strictly guaranteeing zero overbooking even under high concurrent load.
2. **Live Push Projections (Firebase Realtime Database):** Monotonically versioned JSON trees broadcast real-time availability changes and delay notices directly to subscribed clients via WebSockets, eliminating polling overhead on the primary database.
3. **Distributed Regional NoSQL Records (Azure Cosmos DB):** Booking records and telemetry are partitioned geographically by `/region` (e.g. Northern, Western, Southern, Eastern) for low-latency regional reporting, audits, and business intelligence queries.

---

## 2. System Architecture & Component Design

```
+-----------------------------------------------------------------------------------+
|                           CLIENT LAYER (React 19 + TypeScript)                    |
|  - TanStack Query (Server State & Caching)     - Tailwind CSS Custom Theme        |
|  - Lucide React Icons                          - Live Polling & Firebase Streams  |
+-----------------------------------------+-----------------------------------------+
                                          | REST API (JSON)
                                          v
+-----------------------------------------------------------------------------------+
|                         BACKEND SERVICE LAYER (FastAPI)                           |
|  - OAuth2 Password Bearer + JWT Security       - Pydantic v2 Schema Validation     |
|  - SQLAlchemy 2.0 ORM                          - Transactional Boundary Controller |
+------------------+-----------------------------------------------+----------------+
                   |                                               |
         ACID Transactions                                  Outbox CDC Worker
      (SELECT ... FOR UPDATE)                        (Guaranteed At-Least-Once Delivery)
                   v                                               v
+------------------------------------+           +----------------------------------+
|    AUTHORITATIVE RELATIONAL CORE   |           |    CROSS-CLOUD PROJECTIONS       |
|            (MySQL 8)               |           |                                  |
| - Users, Stations, Trains          |           | - Firebase Realtime DB:          |
| - Train Stops, Journeys            |---------->|   Monotonic Live Seat Tree       |
| - Inventory (Capacity, Version)    |           | - Azure Cosmos DB (NoSQL):       |
| - Tickets & Passengers (3NF)       |           |   Partitioned by /region         |
| - Transactional Outbox Table       |           +----------------------------------+
+------------------------------------+
```

### 2.1 Technology Stack Details
| Layer | Technologies Used | Key Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, TanStack React Query, Lucide Icons, Axios | Clean, responsive UI with zero generic AI tropes; real-time search, booking, seat radar, and trends. |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt) | High-performance asynchronous REST API, route calculation, auth, and concurrency enforcement. |
| **Database Core** | MySQL 8 (InnoDB Engine), SQLAlchemy 2.0, Alembic | ACID transactional guarantees, row-level locks, foreign key cascades, 3NF normalization. |
| **Outbox & CDC** | Background Outbox Poller / Worker | Reads unpublished events from `booking_events` table and guarantees asynchronous cloud replication. |
| **NoSQL & Cloud** | Firebase Admin SDK, Azure Cosmos DB Python SDK | Eventual consistency projections and partition-key regional querying. |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX, Concurrent Futures | Stress testing, race-condition verification, and automated E2E validation. |

---

## 3. Database Schema & Data Modeling (3NF Normalization)

The transactional schema is fully normalized into Third Normal Form (3NF) to eliminate insertion, deletion, and update anomalies:

### 3.1 Relational Entities
1. **`users`**: Customer and administrator credentials.
   - `id` (PK, INT)
   - `name` (VARCHAR 100), `email` (VARCHAR 150, UNIQUE INDEX)
   - `password_hash` (VARCHAR 255), `role` (ENUM: 'PASSENGER', 'ADMIN')
   - `created_at` (DATETIME)
2. **`stations`**: Railway junctions and divisional terminals.
   - `id` (PK, INT)
   - `station_code` (VARCHAR 10, UNIQUE INDEX, e.g. 'NDLS', 'BCT', 'HWH', 'MAS', 'SBC', 'CNB', 'BBR')
   - `name` (VARCHAR 100), `region` (VARCHAR 50, INDEX)
3. **`trains`**: Master train schedule definitions.
   - `id` (PK, INT)
   - `train_number` (VARCHAR 10, UNIQUE INDEX, e.g. '12952')
   - `train_name` (VARCHAR 150)
   - `source_station_id` (FK -> stations.id), `destination_station_id` (FK -> stations.id)
   - `active` (BOOLEAN)
4. **`train_stops`**: Ordered intermediate stations along train itineraries.
   - `id` (PK, INT), `train_id` (FK -> trains.id ON DELETE CASCADE), `station_id` (FK -> stations.id)
   - `stop_sequence` (INT, e.g. 1, 2, 3...)
   - `arrival_time` (TIME), `departure_time` (TIME), `distance_km` (INT)
   - `UNIQUE KEY (train_id, stop_sequence)`
5. **`train_journeys`**: Specific dated operational runs for a train.
   - `id` (PK, INT), `train_id` (FK -> trains.id)
   - `travel_date` (DATE), `status` (ENUM: 'SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED')
   - `departure_datetime` (DATETIME), `arrival_datetime` (DATETIME)
   - `UNIQUE KEY (train_id, travel_date)`
6. **`journey_inventory`**: Real-time seat inventory per class.
   - `id` (PK, INT), `journey_id` (FK -> train_journeys.id)
   - `travel_class` (ENUM: 'AC', 'GENERAL')
   - `capacity` (INT, default 10), `available_seats` (INT, default 10)
   - `waitlist_limit` (INT, default 2), `waitlist_count` (INT, default 0)
   - `fare` (DECIMAL 10,2), `version` (INT, optimistic locking counter)
   - `UNIQUE KEY (journey_id, travel_class)`
7. **`tickets`**: Master booking record per transaction.
   - `id` (PK, INT), `pnr` (VARCHAR 12, UNIQUE, Format: 'RSXXXXXX')
   - `user_id` (FK -> users.id), `journey_id` (FK -> train_journeys.id)
   - `travel_class` (ENUM), `passenger_count` (INT), `total_fare` (DECIMAL 10,2)
   - `status` (ENUM: 'CONFIRMED', 'WAITLISTED', 'CANCELLED')
   - `created_at` (DATETIME), `cancelled_at` (DATETIME NULL)
8. **`passengers`**: Individual passengers traveling under a PNR.
   - `id` (PK, INT), `ticket_id` (FK -> tickets.id ON DELETE CASCADE)
   - `full_name` (VARCHAR 100), `age` (INT), `gender` (ENUM)
   - `seat_number` (VARCHAR 10 NULL, e.g. 'AC-1', 'GEN-4')
   - `reservation_status` (ENUM: 'CNF', 'WL', 'CAN'), `waitlist_position` (INT NULL)
9. **`booking_events` (Transactional Outbox)**:
   - `id` (PK, INT), `aggregate_id` (VARCHAR 50, PNR / Train Number)
   - `event_type` (VARCHAR 50: 'BOOKING_CONFIRMED', 'BOOKING_CANCELLED', 'TRAIN_STATUS_UPDATED')
   - `payload` (JSON payload containing full denormalized entity snapshot)
   - `version` (INT), `published` (BOOLEAN), `retry_count` (INT)
   - `created_at` (DATETIME), `processed_at` (DATETIME NULL)

---

## 4. Key Engineering Modules & Algorithms

### 4.1 Concurrency Control & Zero-Overbooking Algorithm
Booking reservations follow strict pessimistic row-level locking to avoid lost updates or double-booking under high concurrent load:
```python
# 1. Begin Database Transaction
# 2. Acquire exclusive pessimistic lock on inventory record
inventory = db.query(JourneyInventory).filter(
    JourneyInventory.journey_id == journey_id,
    JourneyInventory.travel_class == travel_class
).with_for_update().one()

# 3. Evaluate capacity invariants
if inventory.available_seats >= passenger_count:
    # Allocate Confirmed (CNF) Seats
    inventory.available_seats -= passenger_count
    inventory.version += 1
    # Assign seat labels (e.g. AC-1, AC-2)
elif (inventory.available_seats + (inventory.waitlist_limit - inventory.waitlist_count)) >= passenger_count:
    # Allocate Waitlist (WL) Tickets
    inventory.waitlist_count += passenger_count
else:
    # Strict Rejection: Exceeds seat & waitlist capacity
    raise HTTPException(status_code=400, detail="Capacity and Waitlist limit reached.")

# 4. Write Ticket, Passenger records, and Outbox Event in SAME transaction
# 5. Commit Transaction (releases exclusive row lock atomically)
```

### 4.2 Waitlist Cascading on Cancellation
When a passenger cancels a confirmed ticket:
1. The inventory row is locked with `with_for_update()`.
2. The earliest waitlisted passenger (`reservation_status == 'WL'`) is located ordered by `waitlist_position ASC`.
3. The waitlisted passenger is automatically promoted to `CNF` and assigned the vacated seat number.
4. Remaining waitlist positions are recalculated and compacted.
5. `booking_events` publishes `BOOKING_CANCELLED` and `PASSENGER_PROMOTED`.

### 4.3 Intermediate Station Routing Algorithm
Train search is **stop-sequence aware**:
- Users can query not just start and end terminals, but also any intermediate station pairs (e.g., `NDLS -> CNB`, `HWH -> NDLS`, `CNB -> NDLS`).
- The query joins two aliased instances of `TrainStop` (`StopSource` and `StopDest`) and checks:
  $$\text{StopSource.stop\_sequence} < \text{StopDest.stop\_sequence}$$
- This guarantees trains are returned only if they travel in the exact required journey direction.

### 4.4 Transactional Outbox Pattern
- Writing to MySQL and pushing to external cloud systems (Firebase, Cosmos DB) inside the same web request causes dual-write inconsistencies if the network fails midway.
- Instead, the event is saved to `booking_events` inside the atomic MySQL transaction.
- An asynchronous worker (`app/workers/outbox_worker.py`) polls pending events, dispatches them to Firebase and Cosmos DB adapters, and marks them `published = True` upon success.

---

## 5. Frontend Features & User Experience

1. **Train Search (`/` or `/search`):**
   - Source & destination selection with live station code matching.
   - Travel date picker (within the scheduled 7-day window).
   - Quick route recommendation chips (`NDLS → BCT`, `HWH → NDLS`, `NDLS → MAS`, `SBC → NDLS`, etc.).
   - Interactive availability display with color-coded badges (`Available`, `Waitlist`, `Regret/Full`).
2. **Passenger Booking (`/book`):**
   - Dynamic passenger form addition (Name, Age, Gender).
   - Real-time fare calculation with instant validation.
   - Displays clear seat allocation feedback upon confirmation.
3. **My Trips & Ticket Cancellation (`/trips`):**
   - View confirmed and waitlisted PNRs with passenger seat numbers.
   - 1-Click PNR cancellation with automatic refund/fare calculation and instant waitlist re-allocation.
4. **Live Radar (`/live-status`):**
   - Real-time running status of trains with delay minutes and current station markers.
5. **Booking Trends & Analytics (`/trends`):**
   - Interactive Recharts bar and line visualizations.
   - Booking velocity trends (recent minutes vs historical windows).
   - Regional distribution breakdown (Northern, Western, Eastern, Southern railway zones).
6. **Admin Operations Console (`/admin`):**
   - Delay injection and dynamic train status updates (`ON_TIME`, `DELAYED`, `DIVERTED`, `CANCELLED`).
   - Transactional outbox telemetry inspection and manual retry button.
   - Real-time system health checks.

---

## 6. Verification, Testing & Academic Correctness

### 6.1 Automated Concurrency Race Condition Test (`test_mysql_race_condition.py`)
- Simulates 20 concurrent threads attempting to book the last remaining 2 seats simultaneously.
- **Result:** Exactly 2 seats are allocated as confirmed; the remaining requests either take waitlist or are cleanly rejected. Zero double-booking occurs.

### 6.2 End-to-End Automated Test (`verify_e2e.py`)
- Registers test passenger and admin users.
- Searches trains across intermediate pairs (`NDLS -> CNB`).
- Books 2 tickets, verifies seat decrement in database.
- Cancels a ticket and verifies waitlist promotion.
- Confirms outbox event generation and API response contracts.

---

## 7. Instructions for Feeding into an AI Report Generator

When using an external AI tool (such as Gemini 1.5 Pro, ChatGPT, Claude 3.5 Sonnet, or Microsoft Copilot) to generate a full formal academic project report, laboratory file, or viva voce presentation, provide the following prompt:

```text
Act as a Senior Database Architect and Academic Project Lead.
I am providing you with the full technical architecture, schema specifications, and implementation details of "RailSync 360", a cloud-based railway reservation system built for an Advanced Database Management Systems (ADBMS) course.

Based on the provided documentation, generate a comprehensive, publication-grade academic project report including:
1. Title Page, Abstract, and Keywords.
2. Introduction, Problem Definition, and Objectives.
3. Literature Survey & Comparative Analysis of Relational (MySQL) vs NoSQL (Firebase/Cosmos DB).
4. System Architecture Diagram and Detailed Description (Polyglot Persistence + Transactional Outbox Pattern).
5. Detailed Database Design:
   - Entity-Relationship (ER) Model.
   - 3NF Relational Schema with Constraints, Data Types, and Foreign Keys.
   - Document & JSON Tree Schemas for Firebase and Cosmos DB.
6. Core Algorithms & Transactional Concurrency:
   - Step-by-step Pessimistic Row-Level Locking (SELECT ... FOR UPDATE).
   - Waitlist Cascading & Promotion Algorithm.
   - Directional Intermediate Station Traversal Query.
7. Implementation Details & REST API Specifications.
8. Testing & Experimental Results:
   - Concurrency stress testing (preventing race conditions and overbooking).
   - End-to-end booking lifecycle verification.
9. Security & Access Control (Bcrypt, JWT Tokens, Role-Based Access Control).
10. Conclusion, Academic Learnings, and Future Scope.

Use clean Markdown formatting with tables, structured sections, and professional academic prose.
```

