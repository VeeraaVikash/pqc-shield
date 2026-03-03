from fastapi import APIRouter
from app.database import SessionLocal
from app.models.tls_models import ActiveTLSConnection

router = APIRouter()

@router.get("/active")
def get_active_connections():
    db = SessionLocal()

    connections = db.query(ActiveTLSConnection).all()

    result = []
    for c in connections:
        result.append({
            "conn_id": c.id,
            "source": c.source,
            "destination": c.destination,
            "kem": c.kem_algorithm,
            "signature": c.signature_algorithm,
            "mode": c.mode,
            "latency": f"{c.latency_ms}ms",
            "status": c.status
        })

    db.close()
    return result
