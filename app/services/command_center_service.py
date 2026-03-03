from datetime import datetime

from app.database import SessionLocal
from app.models.inventory_models import InventoryAsset

from app.services.risk_service import calculate_risk_score
from app.services.policy_service import calculate_policy_coverage
from app.services.alert_service import get_alert_summary
from app.services.telemetry_service import get_performance_metrics
from app.services.analytics.distribution_engine import get_algorithm_distribution
from app.services.metrics_service import get_latest_metrics_with_delta
from app.services.qos_service import get_latest_qos


# =================================================
# SYSTEM STATUS ENGINE
# =================================================

def evaluate_system_status(alerts_summary):
    if alerts_summary.get("critical", 0) > 0:
        return "CRITICAL"
    elif alerts_summary.get("high", 0) > 0:
        return "DEGRADED"
    else:
        return "ALL SYSTEMS NOMINAL"


# =================================================
# DASHBOARD OVERVIEW (Inventory Layer)
# =================================================

def get_dashboard_overview():
    db = SessionLocal()

    total_assets = db.query(InventoryAsset).count()

    pqc_ready = db.query(InventoryAsset) \
        .filter(InventoryAsset.pqc_readiness >= 85) \
        .count()

    coverage = (pqc_ready / total_assets * 100) if total_assets else 0

    db.close()

    return {
        "total_assets": total_assets,
        "pqc_ready": pqc_ready,
        "coverage_percent": round(coverage, 2)
    }


# =================================================
# COMMAND CENTER AGGREGATOR
# =================================================

def get_command_center_overview():

    overview = get_dashboard_overview()
    risk = calculate_risk_score()

    # Safe policy handling
    try:
        policy = calculate_policy_coverage("pqc-tls-mandate")
    except Exception:
        policy = {"error": "Policy not found"}

    performance = get_performance_metrics()
    alerts = get_alert_summary()
    algorithm_distribution = get_algorithm_distribution()
    metrics = get_latest_metrics_with_delta()
    qos = get_latest_qos()

    system_status = evaluate_system_status(alerts)

    return {
        "system_status": system_status,
        "last_sync": datetime.utcnow().isoformat(),

        "overview": overview,
        "risk": risk,
        "policy": policy,
        "performance": performance,
        "alerts_summary": alerts,
        "algorithm_distribution": algorithm_distribution,
        "metrics": metrics,
        "qos": qos
    }