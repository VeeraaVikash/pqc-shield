from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from app.models.alert_models import Alert


# =========================================================
# ALERT EVALUATION ENGINE
# =========================================================

def evaluate_alerts():
    db = SessionLocal()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    if not handshakes:
        db.close()
        return

    total = len(handshakes)

    failures = len([h for h in handshakes if not h.success])
    failure_rate = failures / total * 100

    latencies = sorted([h.latency_ms for h in handshakes])
    p99 = latencies[int(len(latencies) * 0.99)]

    classic_count = len([h for h in handshakes if h.kem_algorithm == "Classic"])
    fallback_rate = classic_count / total * 100

    _process_alert(
        db, "FAILURE_RATE",
        failure_rate > 1,
        f"Failure rate exceeded 1% ({round(failure_rate,2)}%)",
        "HIGH"
    )

    _process_alert(
        db, "LATENCY_SPIKE",
        p99 > 5,
        f"P99 latency exceeded 5ms ({round(p99,2)}ms)",
        "MEDIUM"
    )

    _process_alert(
        db, "EXCESSIVE_FALLBACK",
        fallback_rate > 15,
        f"Classic TLS fallback rate high ({round(fallback_rate,2)}%)",
        "WARNING"
    )

    db.commit()
    db.close()


# =========================================================
# ALERT PROCESSOR (WITH ESCALATION)
# =========================================================

def _process_alert(db, alert_type, condition, message, base_severity):

    existing = db.query(Alert)\
        .filter(Alert.type == alert_type, Alert.status == "OPEN")\
        .first()

    if condition:

        if existing:
            existing.message = message
            existing.updated_at = datetime.utcnow()
        else:
            new_alert = Alert(
                type=alert_type,
                message=message,
                severity=base_severity,
                status="OPEN"
            )
            db.add(new_alert)

    else:
        if existing:
            existing.status = "RESOLVED"
            existing.resolved_at = datetime.utcnow()


# =========================================================
# ESCALATION ENGINE
# =========================================================

def escalate_alerts():
    db = SessionLocal()

    now = datetime.utcnow()

    open_alerts = db.query(Alert)\
        .filter(Alert.status == "OPEN")\
        .all()

    for alert in open_alerts:

        if not alert.created_at:
            continue

        age = (now - alert.created_at).total_seconds()

        if age > 180 and alert.severity != "CRITICAL":
            alert.severity = "CRITICAL"

        elif age > 60 and alert.severity == "WARNING":
            alert.severity = "HIGH"

    db.commit()
    db.close()


# =========================================================
# ALERT SUMMARY
# =========================================================

def get_alert_summary():
    db = SessionLocal()

    total = db.query(Alert).count()

    open_alerts = db.query(Alert)\
        .filter(Alert.status == "OPEN")\
        .count()

    critical = db.query(Alert)\
        .filter(Alert.severity == "CRITICAL",
                Alert.status == "OPEN")\
        .count()

    high = db.query(Alert)\
        .filter(Alert.severity == "HIGH",
                Alert.status == "OPEN")\
        .count()

    db.close()

    return {
        "total_alerts": total,
        "open_alerts": open_alerts,
        "critical": critical,
        "high": high
    }