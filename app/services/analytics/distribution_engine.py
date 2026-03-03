from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from datetime import datetime, timedelta


def get_algorithm_distribution():
    db = SessionLocal()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return {}

    distribution = {}

    for h in handshakes:
        key = h.kem_algorithm
        distribution[key] = distribution.get(key, 0) + 1

    percent_distribution = {
        algo: round((count / total) * 100, 2)
        for algo, count in distribution.items()
    }

    db.close()

    return percent_distribution