from fastapi import APIRouter
from app.services.kms_service import get_key_metrics, manual_rotate_key

router = APIRouter()

@router.get("/metrics")
def key_metrics():
    return get_key_metrics()

@router.post("/rotate/{key_id}")
def rotate_key(key_id: str):
    return manual_rotate_key(key_id)
