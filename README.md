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

### Task 9: Billing Cycle Engine ✅
* **Objective**: Generate billing cycle records and maintain renewal schedules.
* **Requirements Completed**:
  - **Monthly Renewal Calculation**: Accurately computes `renewal_date` exactly 1 month forward, accounting for month-end calendar boundaries (e.g. Jan 31 -> Feb 28).
  - **Annual Renewal Calculation**: Accurately computes `renewal_date` exactly 1 year forward with leap-year handling.
  - **Store Billing Cycle History**: Generates sequential billing cycle records (`cycle_index`), auto-completing preceding cycles (`status=completed`) and setting the active cycle to `status=pending`.
  - **API Endpoints**:
    - `POST /api/v1/billing-cycles/generate/{subscription_id}`: Generates next billing cycle.
    - `GET /api/v1/billing-cycles/subscription/{subscription_id}`: Retrieves full historical billing cycle records.
* **Deliverable**: Robust Billing Cycle Calculation Service (`app/services/billing_cycle.py`) verified via 4 automated unit tests.

---

### Task 10: Audit Logging Engine ✅
* **Objective**: Track every important billing action with an immutable audit trail.
* **Requirements Completed (All 6 Log Events)**:
  1. **Plan created**: Automatically logs `action="plan_created"` with new pricing and tier configurations.
  2. **Plan updated**: Automatically logs `action="plan_updated"` capturing previous and updated plan values.
  3. **Customer created**: Automatically logs `action="customer_created"` with customer email and details.
  4. **Subscription created**: Automatically logs `action="subscription_created"` with initial plan and status.
  5. **Plan changed**: Automatically logs `action="plan_changed"` with previous plan, new plan, and proration flag.
  6. **Subscription cancelled**: Automatically logs `action="subscription_cancelled"` with immediate or end-of-cycle cancellation parameters.
* **API Endpoints**:
  - `GET /api/v1/audit-logs`: Retrieves immutable audit entries with filtering by `action`, `entity_type`, `customer_id`, and `subscription_id`.
* **Deliverable**: Automated Audit Logging Service (`app/services/audit.py`) verified via 6 automated unit tests.

---

## 🎯 Milestone 2: Billing Operations & Invoicing

### Task 1: Invoice Generation ✅
* **Objective**: Automatically generate itemized invoices for active subscriptions with calculations, filters, and PDF export.
* **Requirements Completed**:
  - **Unique Invoice Numbers**: Formatted sequential identifier `INV-YYYYMM-XXXX` with database uniqueness constraint.
  - **Billing Cycle & Subscription Linkage**: Linked directly to `subscription_id`, `customer_id`, and `billing_cycle_id`.
  - **Financial Calculations**: Accurately computes `subtotal`, configurable `tax` (default 10%), and `total_amount = subtotal + tax`.
  - **Itemized Line Items**: Stores plan fee, billing interval, and line item metadata in `invoice_line_items`.
  - **Status Lifecycle**: Initial status set to `unpaid` (supports `paid`, `unpaid`, `draft`, `void`).
  - **Duplicate Prevention**: Prevents duplicate invoice creation for the same billing cycle.
  - **Automated PDF Generation**: High-quality branded PDF invoices generated using `ReportLab` with dynamic download.
  - **Interactive UI**:
    - "Invoices" tab added to navigation sidebar.
    - Search filter by invoice number, customer name, and email.
    - Status filter (`paid`, `unpaid`, all).
    - Date range filter (start date, end date).
    - Invoice list and detail view modal with itemized line items.
    - One-click PDF download button.
  - **API Endpoints**:
    - `POST /api/v1/invoices/generate`: Generates invoice for active subscription.
    - `GET /api/v1/invoices`: Lists invoices with status, search, and date filters.
    - `GET /api/v1/invoices/{id}`: Detailed invoice breakdown with line items.
    - `GET /api/v1/invoices/{id}/pdf`: Downloads itemized PDF invoice.
* **Deliverable**: Invoice Generation Service (`app/services/invoice.py`), REST APIs (`app/api/endpoints/invoices.py`), and 7 automated unit tests.

---

### Task 2: Proration & Plan Change Logic ✅
* **Objective**: Allow customers to upgrade or downgrade plans mid-cycle and charge them fairly with automated credit/debit proration.
* **Requirements Completed**:
  - **Accurate Mid-Cycle Proration Formula**:
    - Computes `remaining_days` and `remaining_ratio` in the billing cycle.
    - `Unused Plan Credit = Current Price × Remaining Ratio`
    - `New Plan Charge = New Price × Remaining Ratio`
    - `Net Amount Due = New Charge - Unused Credit`
  - **Live Proration Preview**:
    - Previews the exact financial forecast before confirming plan changes.
    - Displays Unused Plan Credit (`-₹500.00`), New Plan Charge (`+₹1000.00`), and Net Amount Due (`₹500.00`).
  - **Automated Adjustment Invoice**:
    - Generates an adjustment invoice with itemized line items:
      - Line Item 1: `PRORATION_CREDIT` (Unused current plan credit).
      - Line Item 2: `PRORATION_DEBIT` (New plan prorated charge).
  - **Subscription Plan Update**: Switches subscription `plan_id` to the new target plan.
  - **Immutable Audit Trail**: Automatically logs `action="plan_changed"` with old plan, new plan, unused credit, new charge, and net amount due.
  - **Plan Change History Timeline**: Tracks and surfaces chronological timeline of previous plan changes (`Pro → Premium` with date and adjustment amount).
  - **Interactive UI**:
    - "Proration & Plans" tab in sidebar.
    - Current plan view with billing interval and cycle renewal dates.
    - Plan upgrade/downgrade selection modal with available plans.
    - Live Proration Preview summary card before confirmation.
    - Previous Plan Changes timeline cards.
  - **API Endpoints**:
    - `POST /api/v1/subscriptions/{id}/proration-preview`: Computes live preview of proration without applying changes.
    - `POST /api/v1/subscriptions/{id}/change-plan`: Executes the plan upgrade/downgrade with proration and creates invoice adjustments.
    - `GET /api/v1/subscriptions/{id}/plan-history`: Retrieves historical timeline of plan changes.
* **Deliverable**: Proration Engine (`app/services/proration.py`), API Endpoints (`app/api/endpoints/subscriptions.py`), and 5 automated unit tests (`tests/test_proration_logic.py`).

---

### Milestone 2 — Task 3: Mock Payment Gateway & Webhooks ✅
* **Objective**: Simulate real payment processing without integrating an actual payment gateway.
* **Requirements Completed**:
  - **Mock Payment Processing**: `POST /api/v1/payments/process` with `{ "invoice_id": ..., "amount": ..., "simulate_mode": "random|success|failure" }`.
    - 80% success / 20% failure probability (or deterministically forced via `simulate_mode`).
    - Generates a unique `TXN-YYYYMMDD-XXXXXXXX` payment reference per transaction.
    - Creates a `Payment` DB record with `status`, `amount`, `payment_reference`, and `created_at`.
  - **Webhook Handler**: `POST /api/v1/webhooks/payment` processes 3 event types:
    - `payment_success` → Invoice: `unpaid → paid` | Subscription: remains `active`.
    - `payment_failed` → Invoice: `unpaid → failed` | Subscription: `active → past_due`.
    - `payment_refunded` → Invoice: `paid → void` | Payment: `success → refunded`.
  - **Payment Query Endpoints**:
    - `GET /api/v1/payments`: List all payment records (filterable by `status`).
    - `GET /api/v1/payments/{id}`: Retrieve full details of a single transaction.
  - **Interactive Frontend (React App)**:
    - **💳 Payments & Webhooks (M2-T3)** sidebar tab with full Payment Dashboard.
    - Payment Dashboard table: Transaction ID | Invoice # | Amount | Status | Date | Details.
    - **Process Payment modal**: Invoice ID, Amount, Simulation Mode (Random / Force Success / Force Failure).
    - Post-payment result card: Transaction ID, Status, Webhook Event, Amount.
    - **Quick Pay panel**: Auto-lists unpaid invoices with one-click "Pay Now" buttons.
    - **Payment Details modal**: Full transaction record — Invoice No, Amount, Status, Transaction ID, Date.
    - **Workflow info card**: Visual step-by-step pipeline display.
  - **API Endpoints**:
    - `POST /api/v1/payments/process`: Simulate a mock payment transaction.
    - `POST /api/v1/webhooks/payment`: Handle webhook events and update invoice/subscription state.
    - `GET /api/v1/payments`: Query all payment transactions.
    - `GET /api/v1/payments/{id}`: Get individual payment details.
* **Deliverable**: Payment Engine (`app/services/payment.py`), Endpoints (`app/api/endpoints/payments.py`, `app/api/endpoints/webhooks.py`), 7 automated unit tests (`tests/test_mock_payment_gateway.py`).

---

## 🛠️ Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── audit_logs.py            # Task 10 Audit log query endpoints
│   │   │   ├── auth.py                  # JWT Auth & User endpoints
│   │   │   ├── billing_cycles.py        # Task 9 Billing cycle endpoints
│   │   │   ├── customers.py             # Customer CRUD endpoints (Task 6)
│   │   │   ├── invoices.py              # Milestone 2 Task 1 Invoice endpoints & PDF export
│   │   │   ├── pages.py                 # Interactive HTML UI pages (Auth, Invoices, Subscriptions & Proration)
│   │   │   ├── payments.py              # Milestone 2 Task 3 Payment processing & query endpoints
│   │   │   ├── plans.py                 # Plan CRUD endpoints (Task 5)
│   │   │   ├── subscriptions.py         # Milestone 2 Task 2 Proration Preview & Plan Change APIs
│   │   │   └── webhooks.py              # Milestone 2 Task 3 Webhook event handler
│   ├── core/                            # Configuration (.env) & Database engine (PostgreSQL/SQLAlchemy)
│   ├── models/                          # 7 Core ORM models (Plans, Customers, Subscriptions, Invoices, etc.)
│   ├── schemas/                         # Pydantic validation schemas (Proration, Invoices, Payments, etc.)
│   ├── services/
│   │   ├── audit.py                     # Task 10 Centralized audit logging service
│   │   ├── billing_cycle.py             # Task 9 Billing cycle calculation service
│   │   ├── invoice.py                   # Milestone 2 Task 1 Invoice generation & ReportLab PDF engine
│   │   ├── payment.py                   # Milestone 2 Task 3 Mock payment engine & webhook handler
│   │   ├── proration.py                 # Milestone 2 Task 2 Proration calculation & plan change engine
│   │   └── state_machine.py             # Task 4 State Machine & transition logic
│   └── main.py                          # FastAPI application entrypoint
├── tests/
│   ├── test_audit_logging.py            # Task 10 Audit logging tests (6 tests)
│   ├── test_auth.py                     # Task 3 JWT Auth tests (3 tests)
│   ├── test_billing_cycle_engine.py     # Task 9 Billing cycle engine tests (4 tests)
│   ├── test_customers_api.py            # Task 6 Customer API tests (3 tests)
│   ├── test_database_schema.py          # Task 2 Schema inspection tests (9 tests)
│   ├── test_invoice_generation.py       # Milestone 2 Task 1 Invoice tests (7 tests)
│   ├── test_mock_payment_gateway.py     # Milestone 2 Task 3 Payment Gateway tests (7 tests)
│   ├── test_plans_api.py                # Task 5 Plan API tests (4 tests)
│   ├── test_proration_logic.py          # Milestone 2 Task 2 Proration tests (5 tests)
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

# Run Billing Cycle Engine Tests (4 tests)
python backend/tests/test_billing_cycle_engine.py

# Run Audit Logging Tests (6 tests)
python backend/tests/test_audit_logging.py

# Run Invoice Generation Tests (Milestone 2 Task 1 - 7 tests)
python backend/tests/test_invoice_generation.py

# Run Proration & Plan Change Tests (Milestone 2 Task 2 - 5 tests)
python backend/tests/test_proration_logic.py

# Run Mock Payment Gateway & Webhook Tests (Milestone 2 Task 3 - 7 tests)
python backend/tests/test_mock_payment_gateway.py

# Or run all 66 tests together:
python -m unittest discover backend/tests
```
