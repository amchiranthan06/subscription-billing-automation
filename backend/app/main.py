from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.api_v1 import api_router
from app.models.models import Plan
from app.models.enums import BillingInterval
from decimal import Decimal

# Automatically create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated Subscription & Billing Engine with Recurring Revenue, Proration, and Webhook Retries",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_default_plans():
    """Initializes standard SaaS pricing tiers if none exist."""
    db = SessionLocal()
    try:
        if db.query(Plan).count() == 0:
            default_plans = [
                Plan(
                    name="Starter Plan",
                    code="starter",
                    description="Essential billing tools for early-stage startups and small projects",
                    price=Decimal("19.00"),
                    billing_interval=BillingInterval.MONTHLY,
                    trial_days=14,
                    feature_entitlements={"api_requests": 10000, "seats": 3, "pdf_invoices": True}
                ),
                Plan(
                    name="Pro Plan",
                    code="pro",
                    description="Complete subscription automation for scaling SaaS businesses",
                    price=Decimal("49.00"),
                    billing_interval=BillingInterval.MONTHLY,
                    trial_days=14,
                    feature_entitlements={"api_requests": 100000, "seats": 10, "pdf_invoices": True, "custom_branding": True}
                ),
                Plan(
                    name="Enterprise Plan",
                    code="enterprise",
                    description="Dedicated billing infrastructure with custom SLAs and audit logs",
                    price=Decimal("99.00"),
                    billing_interval=BillingInterval.MONTHLY,
                    trial_days=14,
                    feature_entitlements={"api_requests": -1, "seats": 50, "dedicated_support": True}
                ),
            ]
            db.add_all(default_plans)
            db.commit()
    finally:
        db.close()

# Seed default plans on startup
seed_default_plans()

# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
