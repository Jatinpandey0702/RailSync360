# RailSync 360 — Cloud Setup & Operation Runbook

## 1. Multi-Database Architecture & Setup

### A. AWS RDS MySQL (Authoritative Core)
1. **Console Provisioning:**
   - Create an Amazon RDS MySQL 8.0 instance (e.g. `db.t4g.micro` for demo / free tier eligible).
   - Set database name: `railsync_db`.
   - In VPC Security Groups, allow inbound TCP port `3306` from the application host or container IP.
2. **Configuration in RailSync 360:**
   - Update `.env`:
     ```env
     DATABASE_URL=mysql+pymysql://<admin-user>:<admin-password>@<rds-endpoint>.rds.amazonaws.com:3306/railsync_db
     ```
   - Run seed script:
     ```powershell
     .\backend\venv\Scripts\python scripts/seed_data.py
     ```

---

### B. Firebase Realtime Database (Live Projections)
1. **Console Setup:**
   - Go to [Firebase Console](https://console.firebase.google.com/) and create a project `RailSync-360`.
   - Under Build, choose **Realtime Database** and create a database (e.g., `us-central1`).
   - Navigate to **Project Settings > Service Accounts**, generate and download a private key JSON.
   - Save the JSON key in `backend/secrets/firebase_service_account.json` (ensure it remains gitignored).
2. **Security Rules:**
   Apply the following rules in the Firebase console:
   ```json
   {
     "rules": {
       "live_seats": {
         ".read": true,
         ".write": false
       },
       "live_trains": {
         ".read": true,
         ".write": false
       },
       "announcements": {
         ".read": true,
         ".write": false
       }
     }
   }
   ```
   *(Allows public read for real-time browser subscriptions; writes are restricted exclusively to the backend Admin SDK).*
3. **Configuration:**
   - Set in `.env`:
     ```env
     FIREBASE_ENABLED=true
     FIREBASE_DATABASE_URL=https://<your-project>-default-rtdb.firebaseio.com/
     FIREBASE_SERVICE_ACCOUNT_KEY=backend/secrets/firebase_service_account.json
     ```

---

### C. Azure Cosmos DB (Distributed Regional NoSQL)
1. **Console Setup:**
   - Create an Azure Cosmos DB for NoSQL account.
   - Database name: `RailSyncRecords`.
   - Container name: `RegionalBookingEvents`.
   - **Partition key:** `/region`.
2. **Configuration:**
   - Obtain the Primary Connection String or Endpoint and Primary Key from Keys blade.
   - Update `.env`:
     ```env
     COSMOS_ENABLED=true
     COSMOS_ENDPOINT=https://<your-account>.documents.azure.com:443/
     COSMOS_KEY=<your-primary-key>
     COSMOS_DATABASE=RailSyncRecords
     COSMOS_CONTAINER=RegionalBookingEvents
     ```

---

## 2. Advanced SQL Demonstrations (Experiment 9)

### Query 1: Journey Route and Schedule Join
```sql
SELECT 
    t.train_number,
    t.train_name,
    s_src.station_code AS source_station,
    s_dst.station_code AS destination_station,
    ts.stop_sequence,
    st.station_code AS stop_station,
    ts.arrival_time,
    ts.departure_time,
    ts.distance_km
FROM trains t
JOIN stations s_src ON t.source_station_id = s_src.id
JOIN stations s_dst ON t.destination_station_id = s_dst.id
JOIN train_stops ts ON ts.train_id = t.id
JOIN stations st ON ts.station_id = st.id
WHERE t.train_number = '12952'
ORDER BY ts.stop_sequence ASC;
```

### Query 2: Concurrency Lock & Pessimistic Seat Allocation
```sql
START TRANSACTION;

-- Pessimistic row-level lock on journey inventory
SELECT id, available_seats, waitlist_count, capacity, waitlist_limit, version
FROM journey_inventory
WHERE journey_id = 1 AND travel_class = 'AC'
FOR UPDATE;

-- Update availability atomically
UPDATE journey_inventory
SET available_seats = available_seats - 1,
    version = version + 1
WHERE id = 1;

-- Insert Outbox Event within same transaction
INSERT INTO booking_events (aggregate_id, event_type, payload, version, firebase_synced, cosmos_synced)
VALUES ('RS-DEMO-001', 'BOOKING_CONFIRMED', '{"pnr": "RS-DEMO-001", "region": "Northern", "seats": 1}', 2, FALSE, FALSE);

COMMIT;
```

### Query 3: EXPLAIN Index Optimization for Route Searches
```sql
EXPLAIN SELECT tj.id, tj.travel_date, t.train_number, inv.available_seats, inv.fare
FROM train_journeys tj
JOIN trains t ON tj.train_id = t.id
JOIN journey_inventory inv ON inv.journey_id = tj.id
WHERE tj.travel_date = '2026-10-31'
  AND t.source_station_id = 1
  AND inv.travel_class = 'AC';
```

---

## 3. Five-Minute Examiner Demonstration Script

1. **Step 1: System Status & Topology**
   - Open browser at `http://127.0.0.1:5173/`.
   - Observe the top diagnostic ribbon: displays `MySQL 8 (Local/RDS)` as Authoritative ACID Core, with transparent fallback status for Firebase and Cosmos DB.

2. **Step 2: Train Search & Station Lookup**
   - Select From: `NDLS` (New Delhi) and To: `BCT` (Mumbai Central).
   - Click "Find Trains" to view all 7 scheduled dated journeys, real-time AC & General seat counters, and transparent fares.

3. **Step 3: User Authentication & Booking**
   - Click "Login" in the navigation bar.
   - Click "Passenger Demo" for instant credential autofill (`passenger@example.com` / `Passenger123!`).
   - Click "Sign In" and return to Search.
   - Click "Book Confirmed Seat" on Train #12952 (Rajdhani Express).
   - Enter passenger name and click "Confirm Reservation".
   - **Show examiner:** The green confirmation modal displays the persisted collision-resistant PNR (`RS...`), confirmed seat assignment (e.g. `AC-6`), and total fare.

4. **Step 4: Self-Service Cancellation & Automatic Promotion**
   - Go to "My Trips / PNR" in navbar.
   - View the active reservation.
   - Click "Cancel Reservation" and confirm.
   - Observe that the ticket transitions to `CANCELLED`, freeing up the seat in MySQL and automatically promoting the next waitlisted passenger in FIFO order.

5. **Step 5: Admin Console & Simulation Injection**
   - Click "Logout" and click "Login" again.
   - Select "Admin Controller" quick-fill (`admin@railsync360.internal` / `AdminPass2026!`).
   - Navigate to "Admin Console".
   - Show the examiner:
     - Real-time cloud connectivity badges.
     - Operational Event Injection: update Platform to `3`, set delay to `20 min`, and click "Broadcast Operational Event".
     - Switch to "Live Radar" tab to observe the instant telemetry update.
     - Inspect the Transactional Outbox Telemetry Log table with sync states.
