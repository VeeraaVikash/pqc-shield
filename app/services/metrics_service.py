from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from app.models.metrics_models import MetricsSnapshot


def persist_metrics_snapshot():
    db = SessionLocal()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return

    avg_latency = sum(h.latency_ms for h in handshakes) / total
    failures = len([h for h in handshakes if not h.success])
    success_rate = (1 - failures / total) * 100

    snapshot = MetricsSnapshot(
        handshakes_per_hour=total,
        avg_latency=round(avg_latency, 2),
        success_rate=round(success_rate, 2)
    )

def get_latest_metrics_with_delta():
    db = SessionLocal()

    snapshots = db.query(MetricsSnapshot)\
        .order_by(MetricsSnapshot.created_at.desc())\
        .limit(2)\
        .all()

    if len(snapshots) < 2:
        db.close()
        return {}

    current = snapshots[0]
    previous = snapshots[1]

    delta_handshakes = current.handshakes_per_hour - previous.handshakes_per_hour
    delta_latency = current.avg_latency - previous.avg_latency

    db.close()

    return {
        "handshakes_per_hour": current.handshakes_per_hour,
        "delta_handshakes": delta_handshakes,
        "avg_latency": current.avg_latency,
        "delta_latency": round(delta_latency, 2),
        "success_rate": current.success_rate
    }

    db.add(snapshot)
    db.commit()
    db.close()