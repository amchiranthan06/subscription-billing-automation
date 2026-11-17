-- =====================================================================
-- Subscription Billing Automation System - PostgreSQL schema (Milestone 1)
-- This is the same design the app creates from app/models.py
-- (run `python -m scripts.init_db`). Kept here as plain SQL for review.
-- =====================================================================

-- ---------- Enum types (status fields are enum-typed) ----------------
CREATE TYPE billing_interval     AS ENUM ('monthly', 'annual');
CREATE TYPE plan_status          AS ENUM ('active', 'archived');
CREATE TYPE subscription_status  AS ENUM ('trial', 'active', 'past_due', 'cancelled');
CREATE TYPE billing_cycle_status AS ENUM ('pending', 'invoiced');
CREATE TYPE invoice_status       AS ENUM ('draft', 'pending', 'paid', 'overdue', 'void');
CREATE TYPE payment_status       AS ENUM ('pending', 'succeeded', 'failed', 'refunded');

-- ---------- plans -----------------------------------------------------
CREATE TABLE plans (
    id                 SERIAL PRIMARY KEY,
    name               VARCHAR(100)     NOT NULL UNIQUE,
    description        TEXT,
    price              NUMERIC(12, 2)   NOT NULL CHECK (price >= 0),
    currency           VARCHAR(3)       NOT NULL DEFAULT 'INR',
    billing_interval   billing_interval NOT NULL,
    trial_period_days  INTEGER          NOT NULL DEFAULT 0 CHECK (trial_period_days >= 0),
    features           JSONB            NOT NULL DEFAULT '{}'::jsonb,   -- feature entitlements
    status             plan_status      NOT NULL DEFAULT 'active',
    created_at         TIMESTAMPTZ      NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ      NOT NULL DEFAULT now(),
    archived_at        TIMESTAMPTZ
);

-- ---------- customers -------------------------------------------------
CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    country     VARCHAR(2)   NOT NULL DEFAULT 'IN',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- subscriptions --------------------------------------------
CREATE TABLE subscriptions (
    id                    SERIAL PRIMARY KEY,
    customer_id           INTEGER             NOT NULL REFERENCES customers (id),
    plan_id               INTEGER             NOT NULL REFERENCES plans (id),
    pending_plan_id       INTEGER             REFERENCES plans (id),     -- plan change scheduled for next cycle
    status                subscription_status NOT NULL DEFAULT 'trial',
    trial_started_at      TIMESTAMPTZ,
    trial_end             TIMESTAMPTZ,
    current_period_start  TIMESTAMPTZ,
    current_period_end    TIMESTAMPTZ,
    is_paused             BOOLEAN             NOT NULL DEFAULT FALSE,
    paused_at             TIMESTAMPTZ,
    cancel_at_period_end  BOOLEAN             NOT NULL DEFAULT FALSE,
    -- timestamps for each state change
    status_changed_at     TIMESTAMPTZ,
    activated_at          TIMESTAMPTZ,
    past_due_at           TIMESTAMPTZ,
    cancelled_at          TIMESTAMPTZ,
    created_at            TIMESTAMPTZ         NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ         NOT NULL DEFAULT now()
);
CREATE INDEX ix_subscriptions_customer_id        ON subscriptions (customer_id);
CREATE INDEX ix_subscriptions_plan_id            ON subscriptions (plan_id);
CREATE INDEX ix_subscriptions_status_period_end  ON subscriptions (status, current_period_end);

-- ---------- billing_cycles ------------------------------------------
CREATE TABLE billing_cycles (
    id                        SERIAL PRIMARY KEY,
    subscription_id           INTEGER              NOT NULL REFERENCES subscriptions (id),
    plan_id                   INTEGER              NOT NULL REFERENCES plans (id),
    cycle_number              INTEGER              NOT NULL,
    period_start              TIMESTAMPTZ          NOT NULL,
    period_end                TIMESTAMPTZ          NOT NULL,
    status                    billing_cycle_status NOT NULL DEFAULT 'pending',
    invoice_job_triggered_at  TIMESTAMPTZ,
    created_at                TIMESTAMPTZ          NOT NULL DEFAULT now(),
    CONSTRAINT uq_cycle_subscription_period UNIQUE (subscription_id, period_start)
);
CREATE INDEX ix_billing_cycles_subscription_id ON billing_cycles (subscription_id);

-- ---------- invoices (logic arrives in Milestone 2) ------------------
CREATE TABLE invoices (
    id                SERIAL PRIMARY KEY,
    invoice_number    VARCHAR(30)    NOT NULL UNIQUE,
    customer_id       INTEGER        NOT NULL REFERENCES customers (id),
    subscription_id   INTEGER        NOT NULL REFERENCES subscriptions (id),
    billing_cycle_id  INTEGER        REFERENCES billing_cycles (id),
    status            invoice_status NOT NULL DEFAULT 'draft',
    currency          VARCHAR(3)     NOT NULL DEFAULT 'INR',
    subtotal          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_amount        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_amount      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    line_items        JSONB          NOT NULL DEFAULT '[]'::jsonb,
    issued_at         TIMESTAMPTZ,
    due_date          TIMESTAMPTZ,
    paid_at           TIMESTAMPTZ,
    pdf_path          VARCHAR(500),
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT now()
);
CREATE INDEX ix_invoices_customer_id     ON invoices (customer_id);
CREATE INDEX ix_invoices_subscription_id ON invoices (subscription_id);

-- ---------- payments (logic arrives in Milestone 2) ------------------
CREATE TABLE payments (
    id                 SERIAL PRIMARY KEY,
    invoice_id         INTEGER        NOT NULL REFERENCES invoices (id),
    customer_id        INTEGER        NOT NULL REFERENCES customers (id),
    amount             NUMERIC(12, 2) NOT NULL,
    currency           VARCHAR(3)     NOT NULL DEFAULT 'INR',
    status             payment_status NOT NULL DEFAULT 'pending',
    gateway_reference  VARCHAR(100),
    failure_reason     VARCHAR(255),
    attempt_number     INTEGER        NOT NULL DEFAULT 1,
    created_at         TIMESTAMPTZ    NOT NULL DEFAULT now(),
    processed_at       TIMESTAMPTZ
);
CREATE INDEX ix_payments_invoice_id  ON payments (invoice_id);
CREATE INDEX ix_payments_customer_id ON payments (customer_id);

-- ---------- audit_logs ----------------------------------------------
CREATE TABLE audit_logs (
    id               SERIAL PRIMARY KEY,
    customer_id      INTEGER REFERENCES customers (id),
    subscription_id  INTEGER REFERENCES subscriptions (id),
    entity_type      VARCHAR(50)  NOT NULL,
    entity_id        INTEGER,
    action           VARCHAR(100) NOT NULL,
    old_value        JSONB,
    new_value        JSONB,
    actor            VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_logs_customer_id     ON audit_logs (customer_id);
CREATE INDEX ix_audit_logs_subscription_id ON audit_logs (subscription_id);
CREATE INDEX ix_audit_logs_action          ON audit_logs (action);
CREATE INDEX ix_audit_logs_created_at      ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_entity          ON audit_logs (entity_type, entity_id);
