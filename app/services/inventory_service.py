import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.inventory_models import InventoryAsset


# ---------------------------
# Seed Initial Inventory
# ---------------------------

def seed_inventory():
    db = SessionLocal()

    if db.query(InventoryAsset).count() > 0:
        db.close()
        return

    asset_types = ["TLS Gateway", "SSH Bastion", "App Server", "Load Balancer"]
    algorithms = [
        "Kyber768 + X25519",
        "Dilithium3",
        "RSA-2048 (Legacy)",
        "ECDSA P-384 (Hybrid)"
    ]

    for i in range(1, 51):  # 50 managed assets
        algo = random.choice(algorithms)

        if "Kyber" in algo or "Dilithium" in algo:
            readiness = random.randint(85, 100)
        elif "Hybrid" in algo:
            readiness = random.randint(60, 80)
        else:
            readiness = random.randint(10, 40)

        asset = InventoryAsset(
            hostname=f"node-{i:03}",
            asset_type=random.choice(asset_types),
            algorithm=algo,
            status="active",
            cert_expiry=datetime.utcnow() + timedelta(days=random.randint(30, 365)),
            pqc_readiness=readiness
        )

        db.add(asset)

    db.commit()
    db.close()


# ---------------------------
# Inventory Metrics Engine
# ---------------------------

def get_inventory_metrics():
    db = SessionLocal()

    assets = db.query(InventoryAsset).all()
    total = len(assets)

    pqc_ready = len([a for a in assets if a.pqc_readiness >= 85])
    hybrid = len([a for a in assets if 50 <= a.pqc_readiness < 85])
    legacy = len([a for a in assets if a.pqc_readiness < 50])

    coverage = (pqc_ready / total * 100) if total else 0

    db.close()

    return {
        "total_assets": total,
        "pqc_ready": pqc_ready,
        "hybrid": hybrid,
        "legacy": legacy,
        "coverage_percent": round(coverage, 2)
    }


# ---------------------------
# Inventory Drift (makes it feel alive during demos)
# ---------------------------

def drift_inventory():
    """Slowly drift PQC readiness and certificate expiry to simulate real changes."""
    db = SessionLocal()
    assets = db.query(InventoryAsset).all()

    for asset in assets:
        # PQC readiness slowly increases (migration in progress)
        if asset.pqc_readiness < 100:
            asset.pqc_readiness = min(100, asset.pqc_readiness + random.randint(0, 2))

        # Occasionally expire a certificate (makes inventory feel alive)
        if random.random() < 0.02:  # 2% chance per asset per tick
            asset.cert_expiry = datetime.utcnow() + timedelta(days=random.randint(1, 7))
            asset.status = "warning"
        elif asset.cert_expiry and asset.cert_expiry < datetime.utcnow() + timedelta(days=7):
            asset.status = "warning"
        elif asset.cert_expiry and asset.cert_expiry < datetime.utcnow():
            asset.status = "expired"

        # Random algorithm migration (simulate policy rollout effect)
        if random.random() < 0.01 and "RSA" in (asset.algorithm or ""):
            asset.algorithm = "Kyber768 + X25519"
            asset.pqc_readiness = 90

    db.commit()
    db.close()
