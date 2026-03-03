from app.database import SessionLocal
from app.models.key_models import KeyRecord


def get_key_summary():
    db = SessionLocal()

    total = db.query(KeyRecord).count()
    pqc_keys = db.query(KeyRecord)\
        .filter(KeyRecord.algorithm.like("%Kyber%"))\
        .count()

    expiring = db.query(KeyRecord)\
        .filter(KeyRecord.days_to_expiry < 30)\
        .count()

    db.close()

    return {
        "total_keys": total,
        "pqc_keys": pqc_keys,
        "expiring_soon": expiring
    }