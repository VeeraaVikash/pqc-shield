from fastapi import APIRouter
from app.database import SessionLocal
from app.models.key_models import Key
from app.services.kms_service import get_key_metrics, manual_rotate_key

router = APIRouter()


@router.get("/metrics")
def key_metrics():
    """Summary stats: total keys, PQC keys, classical, expiring."""
    return get_key_metrics()


@router.get("/keys")
def list_keys():
    """Full list of all keys in the vault with details."""
    db = SessionLocal()
    keys = db.query(Key).all()
    result = []
    for k in keys:
        result.append({
            "id": k.key_id,
            "type": k.key_type,
            "algorithm": k.algorithm,
            "usage": k.usage,
            "status": k.status,
            "rotations": k.rotation_count,
            "auto_rotate": k.auto_rotate,
            "created": k.created_at.isoformat() if k.created_at else None,
            "expires": k.expires_at.strftime("%Y-%m-%d") if k.expires_at else None,
        })
    db.close()
    return result


@router.post("/rotate/{key_id}")
def rotate_key(key_id: str):
    """Manually rotate a specific key by its key_id."""
    return manual_rotate_key(key_id)