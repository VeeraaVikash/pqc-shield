import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.core.scheduler import start_scheduler

# ROUTERS
from app.routes.command_center import router as command_center_router
from app.routes.inventory import router as inventory_router
from app.routes.policy import router as policy_router
from app.routes.tls import router as tls_router
from app.routes.alerts import router as alerts_router
from app.routes.kms import router as kms_router
from app.routes.audit import router as audit_router
from app.routes.dashboard import router as dashboard_router
from app.routes.risk import router as risk_router
from app.routes.auth import router as auth_router
from app.routes.protocols import router as protocols_router
from app.routes.ssh import router as ssh_router
from app.routes.telemetry import router as telemetry_router
from app.routes.websocket import router as ws_router
from app.routes.settings import router as settings_router
from app.routes.metrics_export import router as metrics_router

from app.models.user_models import User
from app.models.settings_models import Setting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QUANSEC Backend",
    description="Enterprise Post-Quantum Cryptography Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================================
# CORS Configuration - Dynamic for Render Deployment
# ============================================================
def get_allowed_origins():
    """Build list of allowed origins from environment."""
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Add Render external URL
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        origins.append(render_url)
        logger.info(f"Added Render URL to CORS: {render_url}")
    
    # Add custom origins from environment variable
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        custom_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
        origins.extend(custom_origins)
        logger.info(f"Added custom CORS origins: {custom_origins}")
    
    # Default Vercel deployments
    origins.extend([
        "https://pqc-shield.vercel.app",
        "https://*.vercel.app",
    ])
    
    return origins

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# ============================================================
# Database Setup
# ============================================================
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

# ============================================================
# Route Registration
# ============================================================
app.include_router(auth_router,           prefix="/api/auth",            tags=["Auth"])
app.include_router(protocols_router,      prefix="/api/protocols",       tags=["Protocols"])
app.include_router(ssh_router,            prefix="/api/ssh",             tags=["SSH"])
app.include_router(settings_router,       prefix="/api/settings",        tags=["Settings"])
app.include_router(telemetry_router,      prefix="/api/telemetry",       tags=["Telemetry"])
app.include_router(metrics_router,        prefix="/api",                 tags=["Prometheus"])
app.include_router(ws_router,             prefix="/api/ws",              tags=["WebSocket"])
app.include_router(command_center_router, prefix="/api/command-center",  tags=["Command Center"])
app.include_router(inventory_router,      prefix="/api/inventory",       tags=["Inventory"])
app.include_router(policy_router,         prefix="/api/policy",          tags=["Policy"])
app.include_router(tls_router,            prefix="/api/tls",             tags=["TLS"])
app.include_router(alerts_router,         prefix="/api/alerts",          tags=["Alerts"])
app.include_router(kms_router,            prefix="/api/kms",             tags=["KMS"])
app.include_router(audit_router,          prefix="/api/audit",           tags=["Audit"])
app.include_router(dashboard_router,      prefix="/api/dashboard",       tags=["Dashboard"])
app.include_router(risk_router,           prefix="/api/risk",            tags=["Risk"])

# ============================================================
# Startup Events
# ============================================================
@app.on_event("startup")
def startup_event():
    """Called when app starts."""
    logger.info("Starting QUANSEC Backend...")
    try:
        start_scheduler()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Scheduler startup error: {e}")

@app.on_event("shutdown")
def shutdown_event():
    """Called when app shuts down."""
    logger.info("Shutting down QUANSEC Backend...")

# ============================================================
# Health & Status Endpoints
# ============================================================
@app.get("/")
def root():
    """Root health check endpoint."""
    environment = os.getenv("ENVIRONMENT", "development")
    return {
        "service": "QUANSEC Backend",
        "version": "1.0.0",
        "status": "running",
        "environment": environment,
        "routes": 16,
        "docs": "/docs",
        "metrics": "/api/metrics",
    }

@app.get("/health")
def health():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "service": "QUANSEC Backend",
        "version": "1.0.0",
    }

@app.get("/api/status")
def api_status():
    """API status endpoint."""
    return {
        "api": "operational",
        "timestamp": str(__import__('datetime').datetime.utcnow()),
    }

# ============================================================
# Error Handlers
# ============================================================
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "detail": "Internal server error",
        "type": type(exc).__name__,
    }
