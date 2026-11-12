# BillFlow — Subscription Billing Automation System

A subscription and billing management system built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy ORM**.

---

## 📋 Completed Milestones

### Task 1: Project Setup and Database Schema Design ✅
* **Objective**: Create the FastAPI project structure and configure PostgreSQL.
* **Requirements Completed**:
  - **FastAPI Project Structure**: Organized into modular directories (`app/core/`, `app/models/`, `app/schemas/`, `app/api/`).
  - **PostgreSQL Connection**: Configured SQLAlchemy engine with connection pooling (`pool_size=10`, `max_overflow=20`) and `pool_pre_ping=True` for connection resilience.
  - **SQLAlchemy ORM**: Configured `declarative_base()` and request-scoped `get_db()` dependency to prevent connection leaks.
  - **Environment Variables (`.env`)**: Managed credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`) using Pydantic `BaseSettings` in `app/core/config.py`.
  - **Swagger/OpenAPI Documentation**: Interactive documentation configured at `/docs` (Swagger UI) and `/redoc` (ReDoc).
* **Deliverable**: Application runs successfully on Uvicorn and connects to PostgreSQL.

---

### Task 2: Database Design ✅
* **Objective**: Design all core billing tables with relational integrity and automated timestamps.
* **Requirements Completed (7 Core Models)**:
  1. **Plans**: Defines subscription tiers.
     - `name`: Plan title (e.g., "Starter Plan", "Pro Plan")
     - `price`: Plan amount with decimal precision
     - `billing_interval`: `monthly` or `annual`
     - `trial_days`: Configurable trial duration (default 14 days)
     - `features`: JSON field for feature entitlements
     - `created_at` & `updated_at`: Automatic timestamp tracking
  2. **Customers**: Subscriber account profiles.
     - `name`: Customer name
     - `email`: Unique indexed customer email
     - `company_name`: Business or organization name
     - `created_at` & `updated_at`: Registration and update timestamps
  3. **Subscriptions**: Tracks lifecycle states (`trial`, `active`, `past_due`, `paused`, `cancelled`) and billing period dates.
  4. **BillingCycles**: Manages recurring cycles, start/end dates, and due dates.
  5. **Invoices**: Itemized financial statements with unique numbering (`INV-XXXX`), tax calculation, and payment status.
  6. **Payments**: Records transaction attempts, gateway references, and retry counters.
  7. **AuditLogs**: Immutable compliance ledger recording state transitions and actor details.
* **Deliverable**: All 7 models designed, mapped with foreign keys, and validated via automated schema inspection tests.

---

## 🛠️ Project Structure

```text
backend/
├── app/
│   ├── api/             # API route endpoints
│   ├── core/            # Configuration (.env) & Database engine (PostgreSQL/SQLAlchemy)
│   ├── models/          # 7 Core ORM models (Plans, Customers, Subscriptions, etc.)
│   ├── schemas/         # Pydantic validation schemas
│   └── main.py          # FastAPI application entrypoint
├── tests/
│   ├── test_database_schema.py    # Task 2 schema validation tests
│   └── test_state_machine.py      # State transition unit tests
└── requirements.txt
```

---

## 🚀 How to Run and Verify

### 1. Start the FastAPI Server
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** to test the interactive Swagger documentation.

### 2. Run Database Schema Verification Tests
```bash
python backend/tests/test_database_schema.py
```
Outputs:
```text
Ran 3 tests in 0.076s - OK
```
*(Confirms all 7 tables and required fields exist in the schema).*
