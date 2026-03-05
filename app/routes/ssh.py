from fastapi import APIRouter
from app.services.ssh_simulator import get_ssh_bastions, get_ssh_sessions, get_ssh_metrics

router = APIRouter()


@router.get("/bastions")
def ssh_bastions():
    """List all SSH bastion hosts with real-time status."""
    return get_ssh_bastions()


@router.get("/sessions")
def ssh_sessions():
    """List all active SSH sessions across bastions."""
    return get_ssh_sessions()


@router.get("/metrics")
def ssh_metrics():
    """Aggregated SSH metrics (total sessions, PQC %, latency)."""
    return get_ssh_metrics()
