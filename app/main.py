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

# Models (ensures tables are created)
from app.models.user_models import User
from app.models.settings_models import Setting

# CREATE APP
app = FastAPI(
    title="PQC Shield Backend",
    description="Enterprise Post-Quantum Cryptography Management Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://pqc-shield.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATABASE
Base.metadata.create_all(bind=engine)

# ALL 16 ROUTES
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

# SCHEDULER
@app.on_event("startup")
def startup_event():
    start_scheduler()

# HEALTH CHECK
@app.get("/")
def root():
    return {
        "service": "PQC Shield Backend",
        "version": "1.0.0",
        "status": "running",
        "routes": 16,
        "docs": "/docs",
        "metrics": "/api/metrics",
    }