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

### Task 4: Subscription Status State Machine ✅
* **Objective**: Implement valid subscription lifecycle transitions.
* **Allowed States**: `trial`, `active`, `past_due`, `cancelled`.
* **Valid Transitions Enforced**:
  - `trial -> active` (Trial converted to active subscription upon payment)
  - `trial -> cancelled` (Subscription cancelled during trial)
  - `active -> past_due` (Payment failure on renewal)
  - `active -> cancelled` (Active customer cancellation)
  - `past_due -> active` (Recovery payment succeeded)
  - `past_due -> cancelled` (Retries exhausted or terminal cancellation)
* **Requirements Completed**:
  - **Prevent Invalid Transitions**: Attempts to perform illegal transitions (e.g. `cancelled -> active` or `trial -> past_due`) raise `InvalidStateTransitionError` with an HTTP 400 Bad Request error.
  - **Status Change Timestamps**: Automatically updates `updated_at` and `cancelled_at` timestamps on state mutations.
  - **Immutable Audit Trail**: Appends detailed transition logs to the `AuditLog` table with old status, new status, transition reason, and actor.
  - **API Endpoint**: `PATCH /api/v1/subscriptions/{id}/status` allows testing transitions directly in Swagger UI.
* **Deliverable**: Robust state machine engine verified via 9 automated unit tests and interactive REST endpoints.

---

### Task 5: Plan Management APIs ✅
* **Objective**: Create APIs to manage subscription plans.
* **APIs Implemented**:
  - **Create Plan**: `POST /api/v1/plans` (validates unique code, sets pricing, trial duration, features JSON, records audit log)
  - **List Plans**: `GET /api/v1/plans` (retrieves all plans with optional `active_only` filter)
  - **Get Plan**: `GET /api/v1/plans/{id}` (fetches single plan details)
  - **Update Plan**: `PUT /api/v1/plans/{id}` (updates pricing, features, entitlements with change tracking)
  - **Archive Plan**: `PATCH /api/v1/plans/{id}/archive` (safely deactivates plan so no new subscriptions can be created)
  - **DELETE Plan**: `DELETE /api/v1/plans/{id}` (deletes unused plans; guards against deleting plans with active subscriptions)
* **Deliverable**: Complete plan lifecycle management verified via 4 automated unit tests and interactive Swagger UI.

---

### Task 6: Customer Management APIs ✅
* **Objective**: Manage SaaS customers.
* **APIs Implemented**:
  - **Create Customer**: `POST /api/v1/customers` (registers customer with `name`, `email`, and `company_name`)
  - **List Customers**: `GET /api/v1/customers` (retrieves all registered customer accounts)
  - **Get Customer**: `GET /api/v1/customers/{id}` (fetches single customer profile)
  - **Update Customer**: `PUT /api/v1/customers/{id}` (updates profile details with email uniqueness validation and audit logging)
* **Deliverable**: Complete customer management lifecycle verified via 3 automated unit tests and interactive Swagger UI.

---

### Task 7: Subscription Creation API ✅
* **Objective**: Create customer subscriptions with plan/customer validation, trial logic, and billing cycle initialization.
* **Requirements Completed**:
  - **Customer & Plan Validation**: Verifies customer exists (HTTP 404) and plan exists and is active (HTTP 400).
  - **Trial Period Calculation**: Automatically sets status to `trial` when `start_with_trial=True`, computing `trial_start` and `trial_end` based on plan or custom trial days. Otherwise sets status directly to `active`.
  - **Billing Cycle Initialization**: Automatically generates the first `BillingCycle` entry in `pending` status with synchronized cycle start and end dates.
  - **Audit Logging**: Logs the subscription creation event in `AuditLog` with customer ID, plan name, and initial status.
  - **API Endpoint**: `POST /api/v1/subscriptions`
* **Deliverable**: Fully validated subscription creation engine verified via 4 automated unit tests and interactive Swagger UI.

---

### Task 8: Subscription Operations APIs ✅
* **Objective**: Provide lifecycle management operations for active customer subscriptions.
* **APIs Implemented**:
  - **Change Plan**: `POST /api/v1/subscriptions/{id}/change-plan` (switches active subscriptions to upgraded/downgraded active plans with audit tracking; rejects inactive plans or duplicate plans).
  - **Pause Subscription**: `POST /api/v1/subscriptions/{id}/pause` (transitions active subscription to `paused` state and records `paused_at` timestamp).
  - **Resume Subscription**: `POST /api/v1/subscriptions/{id}/resume` (transitions paused subscription back to `active` state and clears pause status).
  - **Cancel Subscription**: `POST /api/v1/subscriptions/{id}/cancel` (supports both `immediate` cancellation marking `cancelled_at`, and `end_of_cycle` scheduling setting `cancel_at_period_end=True`).
* **Deliverable**: Complete subscription lifecycle operations verified via 5 automated unit tests and interactive Swagger UI.

---

## 🛠️ Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py                  # JWT Auth & User endpoints
│   │   │   ├── customers.py             # Customer CRUD endpoints (Task 6)
│   │   │   ├── pages.py                 # Interactive HTML pages (Signup, Signin, Home)
│   │   │   ├── plans.py                 # Plan CRUD endpoints (Task 5)
│   │   │   └── subscriptions.py         # Subscription Creation & Operations (Tasks 4, 7, 8)
│   ├── core/                            # Configuration (.env) & Database engine (PostgreSQL/SQLAlchemy)
│   ├── models/                          # 7 Core ORM models (Plans, Customers, Subscriptions, etc.)
│   ├── schemas/                         # Pydantic validation schemas
│   ├── services/                        # State Machine & transition logic
│   └── main.py                          # FastAPI application entrypoint
├── tests/
│   ├── test_auth.py                     # Task 3 JWT Auth tests (3 tests)
│   ├── test_customers_api.py            # Task 6 Customer API tests (3 tests)
│   ├── test_database_schema.py          # Task 2 Schema inspection tests (9 tests)
│   ├── test_plans_api.py                # Task 5 Plan API tests (4 tests)
│   ├── test_state_machine.py            # Task 4 State transition tests (9 tests)
│   ├── test_subscription_creation_api.py# Task 7 Subscription creation tests (4 tests)
│   └── test_subscription_operations_api.py # Task 8 Subscription operations tests (5 tests)
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

# Run Subscription State Machine Tests (9 tests)
python backend/tests/test_state_machine.py

# Run Plan Management API Tests (4 tests)
python backend/tests/test_plans_api.py

# Run Customer Management API Tests (3 tests)
python backend/tests/test_customers_api.py

# Run Subscription Creation API Tests (4 tests)
python backend/tests/test_subscription_creation_api.py

# Run Subscription Operations API Tests (5 tests)
python backend/tests/test_subscription_operations_api.py

# Or run all 37 tests together:
python -m unittest discover backend/tests
```
