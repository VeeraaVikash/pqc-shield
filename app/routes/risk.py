from fastapi import APIRouter
from app.services.risk_service import calculate_risk_score
from app.database import SessionLocal
from app.models.risk_models import RiskHistory

router = APIRouter()

@router.get("/score")
def get_risk_score():
    return calculate_risk_score()

@router.get("/history")
def get_risk_history(limit: int = 50):
    db = SessionLocal()

    records = db.query(RiskHistory)\
        .order_by(RiskHistory.timestamp.desc())\
        .limit(limit)\
        .all()

    db.close()

    return [
        {
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "timestamp": str(r.timestamp)
        }
        for r in records
    ]
