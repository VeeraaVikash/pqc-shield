from fastapi import APIRouter
from app.services.metrics_service import get_latest_metrics_with_delta

router = APIRouter()

@router.get("/full")
def dashboard_full():
    metrics = get_latest_metrics_with_delta()
    return metrics
