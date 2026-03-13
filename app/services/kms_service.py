import uuid
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.key_models import Key, KeyRotationHistory
from app.models.alert_models import Alert
from app.services.audit_service import log_event


# =====================================================
# SEED INITIAL KEYS
# =====================================================

def seed_keys():
    db = SessionLocal()
    try:
        if db.query(Key).count() > 0:
            return

        root_key = Key(
            key_id="ROOT-CA-001",
            key_type="SIG",
            algorithm="Dilithium5",
            usage="Root CA Signing",
            expires_at=datetime.utcnow() + timedelta(days=730),
            auto_rotate=False
        )
        db.add(root_key)
        db.commit()
        db.refresh(root_key)

        algorithms = [
            ("KEM", "Kyber768"),
            ("KEM", "Kyber1024"),
            ("SIG", "Dilithium3"),
            ("SIG", "SPHINCS+-SHA256"),
            ("KEM", "RSA-2048 (Legacy)")
        ]

        for algo_type, algo in algorithms:
            key = Key(
                key_id=f"KEY-{str(uuid.uuid4())[:8]}",
                key_type=algo_type,
                algorithm=algo,
                usage="TLS" if algo_type == "KEM" else "Authentication",
                expires_at=datetime.utcnow() + timedelta(days=180),
                parent_key_id=root_key.id
            )
            db.add(key)

        db.commit()

    except Exception:
        db.rollback()   # FIX: release lock immediately on failure
        raise
    finally:
        db.close()      # FIX: ALWAYS close


# =====================================================
# DEMO KEY (fast-expiring for live rotation during demos)
# =====================================================

def seed_demo_key():
    """Create a fast-expiring demo key (45s) so viewers can watch live rotation."""
    db = SessionLocal()
    try:
        existing = db.query(Key).filter(Key.key_id == "DEMO-KEY-LIVE").first()
        if existing:
            return

        demo_key = Key(
            key_id="DEMO-KEY-LIVE",
            key_type="KEM",
            algorithm="Kyber768",
            usage="Live Demo (auto-rotates every 45s)",
            expires_at=datetime.utcnow() + timedelta(seconds=45),
            auto_rotate=True
        )
        db.add(demo_key)
        db.commit()

    except Exception:
        db.rollback()   # FIX: release lock immediately on failure
        raise
    finally:
        db.close()      # FIX: ALWAYS close


# =====================================================
# KEY METRICS
# =====================================================

def get_key_metrics():
    db = SessionLocal()
    try:
        total = db.query(Key).count()
        pqc = db.query(Key).filter(~Key.algorithm.contains("RSA")).count()
        classical = db.query(Key).filter(Key.algorithm.contains("RSA")).count()
        expiring = db.query(Key)\
            .filter(Key.expires_at < datetime.utcnow() + timedelta(days=30))\
            .count()

        return {
            "total_keys": total,
            "pqc_keys": pqc,
            "classical_keys": classical,
            "expiring_soon": expiring
        }

    finally:
        db.close()      # FIX: ALWAYS close


# =====================================================
# AUTO ROTATION ENGINE
# =====================================================

def auto_rotate_keys():
    db = SessionLocal()
    try:
        keys = db.query(Key).all()

        for key in keys:

            # Expired → rotate
            if key.auto_rotate and key.expires_at < datetime.utcnow():
                key.rotation_count += 1
                key.expires_at = datetime.utcnow() + timedelta(seconds=45) \
                    if key.key_id == "DEMO-KEY-LIVE" \
                    else datetime.utcnow() + timedelta(days=180)
                key.status = "active"

                history = KeyRotationHistory(
                    key_id=key.key_id,
                    reason="AUTO_ROTATION"
                )
                db.add(history)

                alert = Alert(
                    type="KEY_ROTATED",
                    message=f"{key.key_id} auto-rotated",
                    severity="INFO",
                    status="RESOLVED"
                )
                db.add(alert)

            # Warning window
            elif key.expires_at < datetime.utcnow() + timedelta(days=15):
                key.status = "warning"

            # Expired but no auto-rotate
            elif key.expires_at < datetime.utcnow():
                key.status = "expired"

        db.commit()

        # FIX: log_event opens its own session — call AFTER commit+close
        # to avoid two sessions fighting over the DB
        rotated = [k for k in keys if k.auto_rotate and k.status == "active"]
        for key in rotated:
            log_event(
                event_type="KEY_ROTATED",
                description=f"{key.key_id} auto-rotated",
                severity="INFO",
                source="kms_engine"
            )

    except Exception:
        db.rollback()   # FIX: release lock immediately on failure
        raise
    finally:
        db.close()      # FIX: ALWAYS close


# =====================================================
# MANUAL ROTATION
# =====================================================

def manual_rotate_key(key_id):
    db = SessionLocal()
    try:
        key = db.query(Key).filter(Key.key_id == key_id).first()

        if not key:
            return {"error": "Key not found"}

        key.rotation_count += 1
        key.expires_at = datetime.utcnow() + timedelta(days=180)
        key.status = "active"

        history = KeyRotationHistory(
            key_id=key.key_id,
            reason="MANUAL_ROTATION"
        )
        db.add(history)

        db.commit()

    except Exception:
        db.rollback()   # FIX: release lock immediately on failure
        raise
    finally:
        db.close()      # FIX: ALWAYS close

    # FIX: log_event opens its own session — call AFTER this session is closed
    log_event(
        event_type="KEY_ROTATED_MANUAL",
        description=f"{key_id} manually rotated",
        severity="WARNING",
        actor="admin",
        source="kms_engine"
    )

    return {"message": f"{key_id} rotated successfully"}