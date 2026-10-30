# RailSync 360 — Architecture & Data Model

## 1. Multi-Database Topology and Rationale

| Dimension | AWS RDS MySQL 8 (Transactional Core) | Firebase Realtime DB (Live Projections) | Azure Cosmos DB (Distributed Records) |
| :--- | :--- | :--- | :--- |
| **Data Model** | Relational, 3NF Normalized | Hierarchical JSON Tree | Partitioned JSON Documents (NoSQL) |
| **Primary Responsibility** | Single Source of Truth, ACID transactions, inventory locking, seat allocation, PNR registry | Ultra-low-latency real-time client subscriptions, seat availability counters, delay alerts | Regional booking telemetry, geographical analytics, audit events |
| **Consistency Model** | Immediate Consistency (Serializable / Read Committed with row locks) | Eventual Consistency (Monotonically versioned projections) | Session / Bounded Staleness (Documented Cosmos configuration) |
| **Query Pattern** | Complex relational joins, foreign keys, transaction rollbacks | Direct path subscription (`/live_seats/{journey_id}/{class}`) | Partition-key filtered queries (`SELECT * FROM c WHERE c.region = @region`) |
| **Client Access** | Internal Backend only (FastAPI via Connection Pool) | Frontend read-only subscriptions via Firebase JS SDK; Writes restricted to Backend Admin SDK | Backend Azure Cosmos DB Python SDK |

---

## 2. Relational Schema Design (Authoritative MySQL)

### 2.1 Entities & Normalization (3NF)

1. **`users`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `name`: VARCHAR(100) NOT NULL
   - `email`: VARCHAR(150) NOT NULL UNIQUE (indexed)
   - `password_hash`: VARCHAR(255) NOT NULL
   - `role`: ENUM('PASSENGER', 'ADMIN') NOT NULL DEFAULT 'PASSENGER'
   - `created_at`: DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

2. **`stations`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `station_code`: VARCHAR(10) NOT NULL UNIQUE (e.g., 'NDLS', 'BCT', 'MAS')
   - `name`: VARCHAR(100) NOT NULL
   - `region`: VARCHAR(50) NOT NULL (e.g., 'Northern', 'Western', 'Southern')

3. **`trains`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `train_number`: VARCHAR(10) NOT NULL UNIQUE (e.g., '12952', '12301')
   - `train_name`: VARCHAR(150) NOT NULL
   - `source_station_id`: INT NOT NULL, FK -> `stations.id`
   - `destination_station_id`: INT NOT NULL, FK -> `stations.id`
   - `active`: BOOLEAN NOT NULL DEFAULT TRUE

4. **`train_stops`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `train_id`: INT NOT NULL, FK -> `trains.id` ON DELETE CASCADE
   - `station_id`: INT NOT NULL, FK -> `stations.id`
   - `stop_sequence`: INT NOT NULL
   - `arrival_time`: TIME NULL
   - `departure_time`: TIME NULL
   - `distance_km`: INT NOT NULL DEFAULT 0
   - UNIQUE KEY (`train_id`, `stop_sequence`)

5. **`train_journeys`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `train_id`: INT NOT NULL, FK -> `trains.id` ON DELETE CASCADE
   - `travel_date`: DATE NOT NULL
   - `status`: ENUM('SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED') DEFAULT 'SCHEDULED'
   - `departure_datetime`: DATETIME NOT NULL
   - `arrival_datetime`: DATETIME NOT NULL
   - UNIQUE KEY (`train_id`, `travel_date`)

6. **`journey_inventory`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `journey_id`: INT NOT NULL, FK -> `train_journeys.id` ON DELETE CASCADE
   - `travel_class`: ENUM('AC', 'GENERAL') NOT NULL
   - `capacity`: INT NOT NULL DEFAULT 10
   - `available_seats`: INT NOT NULL DEFAULT 10
   - `waitlist_limit`: INT NOT NULL DEFAULT 2
   - `waitlist_count`: INT NOT NULL DEFAULT 0
   - `fare`: DECIMAL(10, 2) NOT NULL
   - `version`: INT NOT NULL DEFAULT 1
   - UNIQUE KEY (`journey_id`, `travel_class`)

7. **`tickets`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `pnr`: VARCHAR(12) NOT NULL UNIQUE (Format: RS360-XXXXXX)
   - `user_id`: INT NOT NULL, FK -> `users.id`
   - `journey_id`: INT NOT NULL, FK -> `train_journeys.id`
   - `travel_class`: ENUM('AC', 'GENERAL') NOT NULL
   - `passenger_count`: INT NOT NULL
   - `total_fare`: DECIMAL(10, 2) NOT NULL
   - `status`: ENUM('CONFIRMED', 'WAITLISTED', 'CANCELLED') NOT NULL
   - `created_at`: DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
   - `cancelled_at`: DATETIME NULL

8. **`passengers`**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `ticket_id`: INT NOT NULL, FK -> `tickets.id` ON DELETE CASCADE
   - `full_name`: VARCHAR(100) NOT NULL
   - `age`: INT NOT NULL
   - `gender`: ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL
   - `seat_number`: VARCHAR(10) NULL (e.g. 'AC-1', 'GEN-4')
   - `reservation_status`: ENUM('CNF', 'WL', 'CAN') NOT NULL
   - `waitlist_position`: INT NULL

9. **`booking_events` (Transactional Outbox)**
   - `id`: INT AUTO_INCREMENT PRIMARY KEY
   - `aggregate_id`: VARCHAR(50) NOT NULL
   - `event_type`: VARCHAR(50) NOT NULL (e.g. 'BOOKING_CONFIRMED', 'BOOKING_CANCELLED', 'SEATS_UPDATED')
   - `payload`: JSON NOT NULL
   - `version`: INT NOT NULL DEFAULT 1
   - `created_at`: DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
   - `firebase_synced`: BOOLEAN NOT NULL DEFAULT FALSE
   - `cosmos_synced`: BOOLEAN NOT NULL DEFAULT FALSE
   - `firebase_error`: TEXT NULL
   - `cosmos_error`: TEXT NULL
   - `attempts`: INT NOT NULL DEFAULT 0

---

## 3. Concurrency & Booking Transaction Algorithm

```sql
START TRANSACTION;

-- Step 1: Pessimistic Row-Level Lock on inventory
SELECT id, available_seats, waitlist_count, capacity, waitlist_limit, version
FROM journey_inventory
WHERE journey_id = :journey_id AND travel_class = :travel_class
FOR UPDATE;

-- Step 2: Validate capacity & determine allocation
-- If available_seats >= requested_count: Status = CONFIRMED
-- Else if waitlist_count + requested_count <= waitlist_limit: Status = WAITLISTED
-- Else ROLLBACK with CapacityExceededException

-- Step 3: Insert Ticket & generate collision-resistant PNR
INSERT INTO tickets (pnr, user_id, journey_id, travel_class, passenger_count, total_fare, status)
VALUES (:pnr, :user_id, :journey_id, :travel_class, :passenger_count, :total_fare, :status);

-- Step 4: Allocate Seat Numbers or Waitlist Positions for Passengers
-- Update journey_inventory counters & increment version
UPDATE journey_inventory
SET available_seats = available_seats - :booked_seats,
    waitlist_count = waitlist_count + :waitlisted_seats,
    version = version + 1
WHERE id = :inventory_id;

-- Step 5: Atomically insert Outbox Event
INSERT INTO booking_events (aggregate_id, event_type, payload, version)
VALUES (:pnr, 'BOOKING_CONFIRMED', :payload_json, :new_version);

COMMIT;
```
