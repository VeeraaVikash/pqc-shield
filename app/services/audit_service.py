from app.database import SessionLocal
from app.models.audit_models import AuditLog


def log_event(event_type, description, severity="INFO",
              actor="system", source="core"):
    db = SessionLocal()
    try:
        entry = AuditLog(
            event_type=event_type,
            description=description,
            severity=severity,
            actor=actor,
            source=source
        )
        db.add(entry)
        db.commit()

    except Exception:
        db.rollback()   # FIX: release lock immediately on failure
        raise
    finally:
        db.close()      # FIX: ALWAYS close — was leaking connections


def get_audit_logs(limit=50):
    db = SessionLocal()
    try:
        logs = db.query(AuditLog)\
            .order_by(AuditLog.timestamp.desc())\
            .limit(limit)\
            .all()

        return [
            {
                "event_type": l.event_type,
                "actor": l.actor,
                "source": l.source,
                "description": l.description,
                "severity": l.severity,
                "timestamp": l.timestamp
            }
            for l in logs
        ]

    finally:
        db.close()      # FIX: ALWAYS close