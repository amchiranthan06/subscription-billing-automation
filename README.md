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
* **Requirements Completed (7 Core Models & Exact Attributes)**:
  1. **Plans**:
     - `name`, `price`, `billing_interval`, `trial_days`, `features`, `created_at`, `updated_at`
  2. **Customers**:
     - `name`, `email`, `company_name`, `created_at`, `updated_at`
  3. **Subscriptions**:
     - `customer_id`, `plan_id`, `status`, `start_date`, `end_date`, `created_at`, `updated_at`
  4. **Billing Cycles**:
     - `subscription_id`, `cycle_start_date`, `cycle_end_date`, `renewal_date`, `status` (pending/completed), `created_at`, `updated_at`
  5. **Invoices**:
     - `invoice_number`, `subscription_id`, `customer_id`, `invoice_date`, `due_date`, `subtotal`, `tax_amount`, `total_amount`, `status` (draft/paid/unpaid/void)
  6. **Payments**:
     - `invoice_id`, `payment_reference`, `amount`, `payment_method`, `status` (pending/success/failed/refunded), `payment_date`, `created_at`, `updated_at`
  7. **Audit Logs**:
     - `entity_type` (plan/subscription/invoice/payment), `entity_id`, `action`, `old_value`, `new_value`, `performed_by`, `created_at`
* **Deliverable**: All 7 models designed, mapped with foreign keys, and validated via 8 automated schema inspection tests.

---

### Task 3: User Authentication ✅
* **Objective**: Create signup, signin, home pages using JWT authentication.
* **Requirements Completed**:
  - **User Model (`users`)**: Fields for `id`, `name`, `email`, `hashed_password`, `role`, `created_at`, `updated_at`.
  - **Password Security**: Implemented secure password hashing and verification using `bcrypt`.
  - **JWT Authentication**: Implemented `HS256` JWT token generation and validation with 24-hour expiration (`app/core/security.py`).
  - **Auth API Endpoints**:
    - `POST /api/v1/auth/signup`: Registers a user, hashes password, and returns a signed JWT token.
    - `POST /api/v1/auth/signin`: Validates credentials and returns a signed JWT token.
    - `GET /api/v1/auth/me`: Protected endpoint requiring `Bearer <token>` to access user profile.
  - **Interactive UI Pages**:
    - **Sign Up Page**: `http://127.0.0.1:8000/auth/signup`
    - **Sign In Page**: `http://127.0.0.1:8000/auth/signin`
    - **Protected Home Page**: `http://127.0.0.1:8000/auth/home` (validates JWT from browser `localStorage` and loads user profile).
* **Deliverable**: Complete JWT authentication lifecycle working across backend APIs, database persistence, and browser UI pages.

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

### 2. Run Verification Tests
```bash
# Run Database Schema Tests (9 tests)
python backend/tests/test_database_schema.py

# Run JWT Authentication Tests (3 tests)
python backend/tests/test_auth.py
```
