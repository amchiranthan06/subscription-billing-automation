from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, check_db_connection
from app.api.api_v1 import api_router
from app.api.endpoints import pages
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("billflow")

# Initialize FastAPI with customized Swagger/OpenAPI documentation
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## BillFlow Subscription Billing Automation Engine
    
    A production-ready recurring billing infrastructure built with **FastAPI** and **PostgreSQL**.
    
    ### Key Features:
    * **Customer & Plan Management**: Define pricing tiers, feature entitlements, and trial periods.
    * **Subscription Lifecycle**: Manage transitions across `trial`, `active`, `past_due`, `paused`, and `cancelled`.
    * **Billing Cycle Engine**: Automated recurring billing runs.
    * **Proration Calculator**: Automatic credit/debit calculation for mid-cycle plan changes.
    * **Dunning & Retries**: Automated 1-3-7 day retry schedule for failed transactions.
    * **ReportLab Invoicing**: Branded, itemized PDF invoice generation.
    * **Compliance Audit Trail**: Immutable event logging for financial reconciliation.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Plans",
            "description": "Create, update, and manage subscription pricing tiers."
        },
        {
            "name": "Customers",
            "description": "Customer profiles and tokenized payment methods."
        },
        {
            "name": "Subscriptions",
            "description": "Subscriber lifecycle, trial periods, pause/resume, and cancellations."
        },
        {
            "name": "Audit Logs",
            "description": "Immutable audit trail of all financial and subscription state changes."
        }
    ]
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Verify database connectivity on startup and initialize schema."""
    logger.info("Initializing BillFlow backend application...")
    db_check = check_db_connection()
    if db_check["status"] == "connected":
        logger.info(f"Successfully connected to {db_check['database']}! Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    else:
        logger.warning(
            f"Could not connect to database on startup: {db_check.get('error')}."
        )

# Mount API routers under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Auth UI Pages (Task 3: Signup, Signin, Home)
app.include_router(pages.router)

@app.get("/", include_in_schema=False)
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "documentation": "/docs"
    }

@app.get("/health", include_in_schema=False)
def health_check():
    return {
        "status": "healthy",
        "service": "FastAPI",
        "version": settings.VERSION
    }

@app.get("/health/db", include_in_schema=False)
def database_health_check():
    return check_db_connection()
