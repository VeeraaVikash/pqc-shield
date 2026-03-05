from fastapi import APIRouter
from app.services.audit_service import get_audit_logs

router = APIRouter()


@router.get("/logs")
def audit_logs():
    """Get all audit log entries."""
    return get_audit_logs()