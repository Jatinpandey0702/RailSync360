# RailSync 360 — Cloud Railway Reservation & Distributed Records System

> **ADBMS Lab Experiment 9 Demonstration**  
> **Multi-Database Topology:** AWS RDS MySQL 8 (Transactional Core) + Firebase Realtime DB (Live Projections) + Azure Cosmos DB (Distributed Regional NoSQL)

---

## 1. Executive Summary

**RailSync 360** is a full-stack, university-scale railway reservation prototype built to demonstrate the distinct engineering responsibilities of three cloud database paradigms:
1. **Authoritative ACID Core (MySQL 8 / AWS RDS):** Handles user credentials, inventory allocations, passenger seating, and cancellations with row-level pessimistic locking (`SELECT ... FOR UPDATE`), preventing double-bookings.
2. **Live Push Projections (Firebase Realtime Database):** Publishes versioned JSON trees for sub-second reactive seat counts, platform assignments, and delay broadcasts.
3. **Regional NoSQL Documents (Azure Cosmos DB):** Partitions booking telemetry by `/region` for low-latency queries and eventual consistency analytics.

---

## 2. Architecture & Database Responsibility Matrix

| Attribute | AWS RDS MySQL 8 | Firebase Realtime DB | Azure Cosmos DB |
| :--- | :--- | :--- | :--- |
| **Paradigm** | Relational / 3NF SQL | Hierarchical JSON Tree | Partitioned JSON Documents (NoSQL) |
| **Role** | System of Record | Live Push Projections | Geo-Replicated Query Telemetry |
| **Transaction Guarantee** | ACID with Row-Level Locking | Single-Path Atomic Updates | Bounded Staleness / Session Consistency |
| **Access Pattern** | Complex Relational Joins & FOR UPDATE | React Client Subscription | Region Partition Key Query (`/region`) |

---

## 3. Quick Start (Running Locally)

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- Docker Desktop (for local MySQL container)

### Step 1: Start MySQL 8 Core
```powershell
docker compose up -d
```
*MySQL is mapped to host port `3307` to avoid conflicts with any existing instances.*

### Step 2: Initialize Database & Seed Data
```powershell
.\backend\venv\Scripts\python scripts/seed_data.py
```
*Seeds 5 Indian railway trains, 7-day scheduled journeys, 10 seats + 2 waitlist per class, and demo accounts.*

### Step 3: Run Concurrency & Integration Tests
```powershell
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\pytest backend\tests -v
.\backend\venv\Scripts\python scripts/verify_e2e.py
```

### Step 4: Start Backend Server
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### Step 5: Start Frontend Application
```powershell
cd frontend
npm run dev
```
- Web Application: `http://127.0.0.1:5173/`

---

## 4. Default Demo Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Passenger** | `passenger@example.com` | `Passenger123!` | Search, book, view trips, cancel PNR |
| **Admin Controller** | `admin@railsync360.internal` | `AdminPass2026!` | Admin console, outbox retry, delay injection |

---

## 5. Academic Demonstration Script

See [docs/runbook.md](docs/runbook.md) for the 5-minute examiner walkthrough and SQL queries with `EXPLAIN` optimization.

---

## 6. Disclaimers
*Educational ADBMS demonstration prototype. Not affiliated with Indian Railways, IRCTC, or any official railway authority.*
