from fastapi import APIRouter
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
def audit_logs():
    return get_audit_logs()