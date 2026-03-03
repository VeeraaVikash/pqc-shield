from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from app.models.qos_models import QoSMetrics
from app.services.audit_service import log_event


def calculate_qos_metrics():
    db = SessionLocal()

    one_day_ago = datetime.utcnow() - timedelta(hours=24)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_day_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return {}

    failures = len([h for h in handshakes if not h.success])
    failed_24h = failures

    classic = len([h for h in handshakes if h.kem_algorithm == "Classic"])

    availability = round(((total - failures) / total) * 100, 2)

    # Simulated MTTR (can improve later)
    mttr = 12 if failures > 0 else 5

    status = "HEALTHY"

    if availability < 99:
        status = "DEGRADED"
    if availability < 95:
        status = "CRITICAL"

    metrics = QoSMetrics(
        availability_30d=availability,
        mttr_seconds=mttr,
        failed_handshakes_24h=failed_24h,
        fallback_triggers_24h=classic,
        replay_attacks_detected=0,
        status=status
    )

    db.add(metrics)
    db.commit()
    db.close()

    log_event(
        event_type="QOS_EVALUATED",
        description=f"QoS evaluated: availability {availability}%",
        severity="INFO",
        source="qos_engine"
    )

    return {
        "availability_24h": availability,
        "mttr_seconds": mttr,
        "failed_handshakes_24h": failed_24h,
        "fallback_triggers_24h": classic,
        "status": status
    }


def get_latest_qos():
    db = SessionLocal()

    latest = db.query(QoSMetrics)\
        .order_by(QoSMetrics.timestamp.desc())\
        .first()

    if not latest:
        db.close()
        return {}

    result = {
        "availability": latest.availability_30d,
        "mttr_seconds": latest.mttr_seconds,
        "failed_handshakes_24h": latest.failed_handshakes_24h,
        "fallback_triggers_24h": latest.fallback_triggers_24h,
        "status": latest.status
    }

    db.close()
    return result