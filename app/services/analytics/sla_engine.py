from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from datetime import datetime, timedelta


def get_sla_metrics():
    db = SessionLocal()

    one_day_ago = datetime.utcnow() - timedelta(hours=24)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_day_ago)\
        .all()

    total = len(handshakes)
    failures = len([h for h in handshakes if not h.success])

    availability = round((1 - failures / total) * 100, 4) if total else 100

    db.close()

    return {
        "availability_24h": availability,
        "failed_handshakes": failures
    }