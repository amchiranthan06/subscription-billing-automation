# BillFlow — Subscription Billing Automation System

An automated subscription and billing system designed around a recurring revenue model. It manages customer subscription lifecycles, automates billing cycles, calculates mid-cycle proration for plan changes, handles failed payment retries, generates PDF invoices, and provides a real-time finance admin dashboard.

---

## 🚀 Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, ReportLab (PDFs), python-dateutil
- **Frontend**: React (Vite), Tailwind CSS, Recharts, Lucide Icons
- **Database**: PostgreSQL / SQLite (via SQLAlchemy ORM)
- **Architecture**: REST API, Webhook processing, Automated Dunning / Retries

---

## 📌 Core Features

1. **Subscription Lifecycle & State Machine**: `trial` → `active` → `past_due` → `cancelled`.
2. **Billing Cycle Engine**: Automated recurring cycle triggers.
3. **Proration Calculator**: Fair billing adjustments when upgrading/downgrading mid-cycle.
4. **Mock Payment Gateway & Webhooks**: Simulates real payment gateways with asynchronous event processing.
5. **Dunning & Retry Logic**: Configurable 1-3-7 day retry schedule for failed transactions.
6. **ReportLab PDF Invoices**: Itemized tax invoices with direct download.
7. **Admin Dashboard**: Real-time MRR, churn rate, failed payment queue, and invoice tracking.

---

## 🛠️ Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config & database setup
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic (proration, retry, invoices)
│   └── requirements.txt
├── frontend/             # React (Vite) admin dashboard
└── README.md
```
