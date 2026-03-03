from app.database import SessionLocal
from app.models.inventory_models import InventoryAsset


def get_pqc_rollout_status():
    db = SessionLocal()

    assets = db.query(InventoryAsset).all()

    total = len(assets)

    pqc_only = len([a for a in assets if a.pqc_readiness >= 90])
    hybrid = len([a for a in assets if 50 <= a.pqc_readiness < 90])
    legacy = len([a for a in assets if a.pqc_readiness < 50])

    db.close()

    return {
        "pqc_only_percent": round(pqc_only / total * 100, 2) if total else 0,
        "hybrid_percent": round(hybrid / total * 100, 2) if total else 0,
        "legacy_percent": round(legacy / total * 100, 2) if total else 0
    }