from fastapi import APIRouter
from app.database import SessionLocal
from app.models.alert_models import Alert

router = APIRouter()

@router.get("/")
def get_alerts():
    db = SessionLocal()
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(20).all()

    result = []
    for a in alerts:
        result.append({
            "type": a.type,
            "message": a.message,
            "severity": a.severity,
            "status": a.status,
            "timestamp": str(a.created_at) if a.created_at else None
        })

    db.close()
    return result
