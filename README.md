# RailSync 360 — Cloud Railway Reservation & Distributed Records System

> **Polyglot Database Architecture:** MySQL 8 (ACID Transactional Core) + Firebase Realtime DB (Live Push Projections) + Azure Cosmos DB (Distributed Regional NoSQL)  
> **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2  
> **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, TanStack React Query, Lucide Icons  
> **Repository:** [https://github.com/Jatinpandey0702/RailSync360](https://github.com/Jatinpandey0702/RailSync360)

---

## 1. Executive Summary

**RailSync 360** is a full-stack, enterprise-grade railway reservation and distributed live-inventory prototype. It demonstrates how to combine relational transactional safety with cloud-native distributed data models:

1. **Authoritative ACID Core (MySQL 8):** Normalized to 3rd Normal Form (3NF). Manages users, stations, trains, stops, and inventory. Implements pessimistic row-level locking (`SELECT ... FOR UPDATE`) to strictly prevent race conditions and overbooking.
2. **Live Push Projections (Firebase Realtime Database):** Monotonically versioned JSON trees broadcast sub-second seat availability and train delay updates directly to frontend clients via WebSockets, eliminating heavy polling on the relational core.
3. **Regional NoSQL Documents (Azure Cosmos DB):** Telemetry and booking records partitioned by `/region` (Northern, Western, Southern, Eastern) for low-latency regional reporting, audits, and business intelligence.
4. **Transactional Outbox Pattern:** Ensures dual-write consistency between the ACID MySQL core and downstream NoSQL projections without distributed two-phase commit overhead.

---

## 2. Multi-Database Responsibility Matrix

| Feature / Metric | MySQL 8 Core (InnoDB) | Firebase Realtime DB | Azure Cosmos DB |
| :--- | :--- | :--- | :--- |
| **Data Model** | Relational, 3NF Normalized | Hierarchical JSON Tree | Partitioned JSON Documents |
| **Role in System** | System of Record (Authoritative) | Live Push Projections | Geo-Replicated Query Telemetry |
| **Consistency Level** | Immediate Consistency (ACID) | Eventual Consistency | Bounded Staleness / Session |
| **Concurrency Mechanism** | Pessimistic Locking (`with_for_update`) | Monotonic Atomic Overwrite | Partition Key Partitioning (`/region`) |
| **Primary Access Pattern** | Relational Joins & Booking Transactions | WebSocket Path Subscriptions | SQL-like Document Filters on Partition |
| **Client Access** | FastAPI Backend Connection Pool | Direct Client JS SDK / Admin SDK | Backend Python SDK |

---

## 3. Key Features & Highlights

- **Intermediate Station Traversal:** Intelligent route queries matching stops by sequence (`StopSource.stop_sequence < StopDest.stop_sequence`). Users can search for journeys between intermediate halts (e.g. `NDLS -> CNB`, `CNB -> NDLS`, `BBR -> BCT`) as well as major termini (`NDLS -> BCT`, `HWH -> NDLS`).
- **Strict Concurrency Protection:** High-load booking concurrency tests (`test_mysql_race_condition.py`) prove zero overbooking even under simultaneous 20-thread stress tests.
- **Automated Waitlist Cascading:** Cancelling a confirmed ticket immediately locks the inventory row, promotes the earliest waitlisted passenger (`WL` $\rightarrow$ `CNF`), reclaims the seat, and compacts remaining queue positions.
- **Live Running Radar:** Visualizes train status, delays, and current station markers in real time.
- **Booking Velocity & Regional Analytics:** Interactive dashboards displaying booking velocity (1-min, 5-min, 15-min windows) and zonal passenger distribution.
- **Role-Based Access Control:** Secure JWT authentication with Bcrypt password hashing separating passenger actions from administrative controls.

---

## 4. Local Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- Docker Desktop (for MySQL 8 container)

### Step 1: Start the MySQL Database Container
```powershell
docker compose up -d
```
*MySQL is mapped to host port `3307` to avoid port collisions with any local MySQL service.*

### Step 2: Initialize Database & Seed Sample Records
```powershell
.\backend\venv\Scripts\python scripts/seed_data.py
```
*Seeds master Indian railway stations (NDLS, BCT, HWH, MAS, SBC, CNB, BBR), 5 express trains, 7-day scheduled journeys, coach inventories, and demo accounts.*

### Step 3: Run Concurrency & Integration Tests
```powershell
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest backend\tests -v
.\backend\venv\Scripts\python scripts/verify_e2e.py
```

### Step 4: Run the Backend API Server
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### Step 5: Run the Frontend Development Server
```powershell
cd frontend
npm run dev
```
- Open application: `http://127.0.0.1:5173/`

---

## 5. Demo Credentials

| Role | Email | Password | Permissions & Capabilities |
| :--- | :--- | :--- | :--- |
| **Passenger** | `passenger@example.com` | `Passenger123!` | Search trains, book seats, view trips, cancel PNR |
| **Admin** | `admin@railsync.internal` | `admin123` | Operational delay updates, outbox queue telemetry, system health |

---

## 6. Project Structure

```
RailSync360/
├── backend/
│   ├── app/
│   │   ├── api/endpoints.py          # REST endpoints (Search, Book, Cancel, Trends, Live Status)
│   │   ├── core/                     # Database engine, JWT security, configuration settings
│   │   ├── integrations/             # Firebase & Azure Cosmos DB cloud adapters
│   │   ├── models/entities.py        # SQLAlchemy 3NF models (Users, Trains, Inventory, Outbox)
│   │   ├── schemas/schemas.py        # Pydantic v2 request/response schemas
│   │   ├── services/booking_service.py # Core transactional booking & cancellation logic
│   │   └── workers/outbox_worker.py  # Asynchronous background CDC outbox dispatcher
│   ├── tests/                        # Concurrency race condition & unit tests
│   └── requirements.txt              # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/               # Navbar, UI elements, common components
│   │   ├── context/AuthContext.tsx   # React authentication context & state
│   │   ├── pages/                    # Search, Booking, Trips, LiveRadar, Trends, AdminConsole
│   │   └── services/api.ts           # Axios client with JWT interceptor & TypeScript models
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── PROJECT_REPORT_GUIDE.md       # Comprehensive academic project report guide & prompt
│   ├── architecture.md               # Detailed architectural specs and ER descriptions
│   ├── requirements.md               # Functional & non-functional requirements
│   └── runbook.md                    # Examiner walkthrough & SQL query verification scripts
├── scripts/
│   ├── seed_data.py                  # Database seeder with realistic test schedules
│   └── verify_e2e.py                 # Automated end-to-end booking verification script
├── docker-compose.yml                # MySQL 8 container configuration on port 3307
└── README.md
```

---

## 7. Generating a Complete Academic Project Report

For generating an academic thesis, project report, or laboratory file using an external AI tool (e.g. Gemini 1.5 Pro, ChatGPT, Claude 3.5 Sonnet), refer to:
👉 **[docs/PROJECT_REPORT_GUIDE.md](docs/PROJECT_REPORT_GUIDE.md)**

It contains:
- Complete system design details, mathematical formulations, and algorithm workflows.
- 3NF relational normalization tables and constraint definitions.
- Concurrency evaluation results and SQL execution plans (`EXPLAIN`).
- Ready-to-use prompt templates for generating standard academic report chapters.

---

## 8. Disclaimer
*This project is an educational engineering prototype developed for demonstrating advanced database management and distributed system concepts. It is not affiliated with Indian Railways, IRCTC, or any official railway authority.*
