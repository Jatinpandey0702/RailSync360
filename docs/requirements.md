# RailSync 360 — Requirements Specification

## 1. Project Overview & Objective
RailSync 360 is an advanced railway reservation, live seat availability, and distributed records prototype built for academic demonstration (ADBMS Lab Experiment 9) and professional architectural evaluation. It demonstrates the complementary strengths of three cloud storage models:
1. **AWS RDS MySQL 8 (Transactional Core):** Authoritative single-source-of-truth for inventory, seat allocation, bookings, passengers, stations, and trains with strict ACID guarantees and row-level pessimistic locking (`SELECT ... FOR UPDATE`).
2. **Firebase Realtime Database (Live Projections):** Hierarchical JSON-tree live projections for real-time seat availability, train delay updates, and station platform announcements, subscribed reactively on client browsers without polling.
3. **Azure Cosmos DB (Regional Document Store):** NoSQL document store partitioned by `/region` storing non-sensitive regional booking events and analytics for low-latency queries and eventual consistency comparison.

---

## 2. Core Functional Requirements

### 2.1 Passenger Experience
- **Journey Search:** Search upcoming trains across Indian rail hubs for the next 7 days, filtered by Class (`AC`, `GENERAL`).
- **Deterministic Seat Inventory:** 10 seats per class with 2 waitlist positions per class/journey.
- **Seat Allocation & Locking:** Concurrency-safe reservation ensuring no double bookings, with deterministic collision-resistant PNR generation.
- **Booking Management:** Real-time PNR retrieval, passenger assignment breakdown, and self-service cancellation with automatic FIFO promotion of waiting list reservations.
- **Live Seat Availability Matrix:** Sub-second reactive seat counts updated across concurrent browser tabs.

### 2.2 Operational & Administrative Functions
- **Role-Based Access Control:** Separate standard passenger (`PASSENGER`) and controller/examiner (`ADMIN`) accounts.
- **Journey & Train Scheduling:** Administrative management of dated journeys and inventory initialization.
- **Synthetic Running Status & Delays:** Simulation of platform changes, delays, and service announcements published to Firebase live tree.
- **Outbox Sync Engine:** Transactional outbox polling pattern syncing committed booking events to Firebase and Azure Cosmos DB with status tracking and manual retry capability.
- **Regional Document Queries:** Query regional booking telemetry partitioned by region in Cosmos DB NoSQL.
- **Cloud Service Diagnostics:** Honest connection status, latency, sync lag, and fallback indicator.

---

## 3. Architecture & Separation of Concerns
```
+-------------------------------------------------------------+
|                 Frontend (React + Vite + TS)                |
|  - TanStack Query (REST API State)                          |
|  - Firebase Client SDK (Subscribed Live Availability)       |
|  - Human-Crafted Indian Rail Architectural Design System    |
+--------------+------------------------------+---------------+
               |                              ^
          REST API calls                 Firebase Push
               v                              |
+------------------------------------+        |
|     FastAPI Backend (Python 3.12)  |        |
|  - SQLAlchemy 2 + Alembic          |        |
|  - Pessimistic Locking Concurrency |        |
|  - Transactional Outbox Pattern    |        |
+--------------+---------------------+        |
               |                              |
      ACID Transactions                       |
               v                              |
+-----------------------------+               |
|  Authoritative MySQL 8 DB   |               |
|  (Local Docker / AWS RDS)   |               |
+--------------+--------------+               |
               | Outbox Polling               |
               v                              |
+-----------------------------+               |
| Outbox Worker Dispatcher    +---------------+
|  - Firebase Admin SDK       |
|  - Azure Cosmos DB SDK      +---------------+
+-----------------------------+               |
                                              v
                               +-----------------------------+
                               | Azure Cosmos DB (NoSQL)     |
                               | Partition Key: /region      |
                               +-----------------------------+
```
