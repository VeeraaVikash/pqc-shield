import random
import uuid
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake, ActiveTLSConnection


# =================================================
# TLS HANDSHAKE GENERATOR
# =================================================

def generate_tls_handshake():
    db = SessionLocal()

    kem_choices = ["Kyber768", "Kyber768+X25519", "Classic"]
    kem = random.choices(
        kem_choices,
        weights=[0.75, 0.23, 0.02]
    )[0]

    signature = "Dilithium3" if "Kyber" in kem else "ECDSA-P256"
    latency = round(random.uniform(1.2, 4.5), 2)
    success = random.random() > 0.003

    connection_id = str(uuid.uuid4())

    handshake = TLSHandshake(
        connection_id=connection_id,
        kem_algorithm=kem,
        signature_algorithm=signature,
        latency_ms=latency,
        success=success,
        fallback_triggered=(kem == "Classic"),
        timestamp=datetime.utcnow()
    )

    db.add(handshake)

    mode = "Classic" if kem == "Classic" else \
           "Hybrid" if "+" in kem else \
           "PQC-Only"

    active = ActiveTLSConnection(
        id=connection_id,
        source="client-app",
        destination="api.pqc-vault.io",
        kem_algorithm=kem,
        signature_algorithm=signature,
        mode=mode,
        latency_ms=latency,
        status="active",
        last_seen=datetime.utcnow()
    )

    db.add(active)

    db.commit()
    db.close()


# =================================================
# CLEANUP STALE SESSIONS (REQUIRED BY SCHEDULER)
# =================================================

def cleanup_stale_sessions():
    db = SessionLocal()
    now = datetime.utcnow()

    sessions = db.query(ActiveTLSConnection).all()

    for s in sessions:
        if now - s.last_seen > timedelta(seconds=15):
            s.status = "inactive"

        if now - s.last_seen > timedelta(seconds=60):
            db.delete(s)

    db.commit()
    db.close()


# =================================================
# PERFORMANCE METRICS
# =================================================

def get_performance_metrics():
    db = SessionLocal()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return {}

    failures = len([h for h in handshakes if not h.success])
    failure_rate = failures / total * 100

    latencies = sorted([h.latency_ms for h in handshakes])
    p50 = latencies[int(len(latencies) * 0.5)]
    p99 = latencies[int(len(latencies) * 0.99)]

    db.close()

    return {
        "success_rate": round(100 - failure_rate, 2),
        "failure_rate": round(failure_rate, 2),
        "p50_latency": round(p50, 2),
        "p99_latency": round(p99, 2)
    }