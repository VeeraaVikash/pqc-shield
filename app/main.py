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

# =================================================
# CREATE APP
# =================================================

app = FastAPI(
    title="PQC Shield Backend",
    version="1.0.0"
)

# =================================================
# CORS — Allow Next.js frontend
# =================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://pqc-shield.vercel.app",   # Add your Vercel URL
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================
# DATABASE INIT
# =================================================

Base.metadata.create_all(bind=engine)

# =================================================
# REGISTER ROUTERS
# =================================================

app.include_router(command_center_router, prefix="/api/command-center", tags=["Command Center"])
app.include_router(inventory_router,      prefix="/api/inventory",       tags=["Inventory"])
app.include_router(policy_router,         prefix="/api/policy",          tags=["Policy"])
app.include_router(tls_router,            prefix="/api/tls",             tags=["TLS"])
app.include_router(alerts_router,         prefix="/api/alerts",          tags=["Alerts"])
app.include_router(kms_router,            prefix="/api/kms",             tags=["KMS"])
app.include_router(audit_router,          prefix="/api/audit",           tags=["Audit"])
app.include_router(dashboard_router,      prefix="/api/dashboard",       tags=["Dashboard"])
app.include_router(risk_router,           prefix="/api/risk",            tags=["Risk"])

# =================================================
# START SCHEDULER ON STARTUP
# =================================================

@app.on_event("startup")
def startup_event():
    start_scheduler()

# =================================================
# ROOT HEALTH CHECK
# =================================================

@app.get("/")
def root():
    return {
        "message": "PQC Shield Backend Running",
        "status": "OK"
    }
