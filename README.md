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
Ran 8 tests in 0.060s - OK
```
*(Confirms all 7 tables and all required fields exist in the schema).*
