from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.policy_models import Policy
from app.models.inventory_models import InventoryAsset
from app.models.alert_models import Alert
from app.models.tls_models import TLSHandshake
from app.services.audit_service import log_event


# =====================================================
# SEED DEFAULT POLICY
# =====================================================

def seed_policies():
    db = SessionLocal()

    if db.query(Policy).count() > 0:
        db.close()
        return

    policy = Policy(
        name="pqc-tls-mandate",
        target_group="TLS Gateway",
        required_kem="Kyber768",
        required_signature="Dilithium3",
        enforcement="STRICT",
        rollout_strategy="CANARY",
        canary_percentage=50,
        fallback_allowed=True,
        sunset_date=datetime(2026, 6, 1),
        status="ACTIVE"
    )

    db.add(policy)
    db.commit()
    db.close()


# =====================================================
# POLICY COVERAGE ENGINE
# =====================================================

def calculate_policy_coverage(policy_name):
    db = SessionLocal()

    policy = db.query(Policy).filter(Policy.name == policy_name).first()

    if not policy:
        db.close()
        return {"error": "Policy not found"}

    assets = db.query(InventoryAsset)\
        .filter(InventoryAsset.asset_type == policy.target_group)\
        .all()

    compliant = 0

    for asset in assets:
        if policy.required_kem in asset.algorithm:
            compliant += 1

    coverage = (compliant / len(assets) * 100) if assets else 0

    db.close()

    return {
        "policy": policy.name,
        "target_group": policy.target_group,
        "coverage_percent": round(coverage, 2),
        "total_assets": len(assets),
        "compliant_assets": compliant
    }


# =====================================================
# POLICY ENFORCEMENT
# =====================================================

def enforce_policy_on_handshake(handshake):
    db = SessionLocal()

    policies = db.query(Policy)\
        .filter(
            Policy.target_group == "TLS Gateway",
            Policy.status == "ACTIVE"
        ).all()

    for policy in policies:

        # STRICT enforcement
        if policy.enforcement == "STRICT":
            if policy.required_kem not in handshake.kem_algorithm:

                _create_alert_if_not_exists(
                    db,
                    "POLICY_VIOLATION",
                    f"{policy.name} violated: Required {policy.required_kem}, got {handshake.kem_algorithm}",
                    "HIGH"
                )

                log_event(
                    event_type="POLICY_VIOLATION",
                    description=f"{policy.name} violated for {handshake.kem_algorithm}",
                    severity="CRITICAL",
                    source="policy_engine"
                )

        # Sunset enforcement
        if policy.sunset_date and datetime.utcnow() > policy.sunset_date:
            if "Classic" in handshake.kem_algorithm:

                _create_alert_if_not_exists(
                    db,
                    "SUNSET_VIOLATION",
                    f"Classical fallback used after sunset for policy {policy.name}",
                    "CRITICAL"
                )

                log_event(
                    event_type="SUNSET_VIOLATION",
                    description=f"Sunset violation for {policy.name}",
                    severity="CRITICAL",
                    source="policy_engine"
                )

    db.commit()
    db.close()


# =====================================================
# FALLBACK THRESHOLD MONITORING
# =====================================================

def evaluate_fallback_threshold(threshold=15):
    db = SessionLocal()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return

    classic = len([h for h in handshakes if h.kem_algorithm == "Classic"])
    fallback_rate = classic / total * 100

    if fallback_rate > threshold:

        _create_alert_if_not_exists(
            db,
            "EXCESSIVE_FALLBACK",
            f"Fallback rate {round(fallback_rate, 2)}% exceeds threshold {threshold}%",
            "CRITICAL"
        )

        log_event(
            event_type="EXCESSIVE_FALLBACK",
            description=f"Fallback exceeded {threshold}%",
            severity="CRITICAL",
            source="policy_engine"
        )

    db.commit()
    db.close()


# =====================================================
# ALERT HELPER
# =====================================================

def _create_alert_if_not_exists(db, alert_type, message, severity):
    existing = db.query(Alert)\
        .filter(Alert.type == alert_type, Alert.status == "OPEN")\
        .first()

    if not existing:
        alert = Alert(
            type=alert_type,
            message=message,
            severity=severity,
            status="OPEN"
        )
        db.add(alert)


# =====================================================
# SIMULATED POLICY ROLLOUT
# =====================================================

def rollout_policy_to_assets(policy_name, target_percentage=90):
    db = SessionLocal()

    policy = db.query(Policy).filter(Policy.name == policy_name).first()

    if not policy:
        db.close()
        return {"error": "Policy not found"}

    assets = db.query(InventoryAsset)\
        .filter(InventoryAsset.asset_type == policy.target_group)\
        .all()

    total = len(assets)
    required_compliant = int((target_percentage / 100) * total)

    compliant = [a for a in assets if policy.required_kem in a.algorithm]
    needed = required_compliant - len(compliant)

    for asset in assets:
        if needed <= 0:
            break
        if policy.required_kem not in asset.algorithm:
            asset.algorithm = f"{policy.required_kem} + X25519"
            asset.pqc_readiness = 95
            needed -= 1

    db.commit()
    db.close()

    return {
        "status": "Rollout completed",
        "target_percentage": target_percentage
    }