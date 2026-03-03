from fastapi import APIRouter
from app.database import SessionLocal
from app.models.inventory_models import InventoryAsset
from app.services.inventory_service import get_inventory_metrics

router = APIRouter()

@router.get("/overview")
def inventory_overview():
    return get_inventory_metrics()

@router.get("/assets")
def list_assets():
    db = SessionLocal()
    assets = db.query(InventoryAsset).all()

    result = []
    for a in assets:
        result.append({
            "id": a.id,
            "hostname": a.hostname,
            "type": a.asset_type,
            "algorithm": a.algorithm,
            "status": a.status,
            "cert_expiry": str(a.cert_expiry.date()) if a.cert_expiry else None,
            "pqc_readiness": a.pqc_readiness
        })

    db.close()
    return result
