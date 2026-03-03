from apscheduler.schedulers.background import BackgroundScheduler
from app.services.telemetry_service import generate_tls_handshake, cleanup_stale_sessions
from app.services.alert_service import evaluate_alerts
from app.services.risk_service import persist_risk_snapshot
from app.services.inventory_service import seed_inventory
from app.services.policy_service import seed_policies
from app.services.alert_service import escalate_alerts
from app.services.metrics_service import persist_metrics_snapshot
from app.services.kms_service import auto_rotate_keys
from app.services.qos_service import calculate_qos_metrics
scheduler = BackgroundScheduler()


def start_scheduler():

    # Seed initial data
    seed_inventory()
    seed_policies()
    auto_rotate_keys()
    calculate_qos_metrics()

    # Telemetry
    scheduler.add_job(generate_tls_handshake, "interval", seconds=1)
    scheduler.add_job(cleanup_stale_sessions, "interval", seconds=5)

    
    # Alert monitoring
    scheduler.add_job(evaluate_alerts, "interval", seconds=10)

    # Escalation engine
    scheduler.add_job(escalate_alerts, "interval", seconds=15)
    scheduler.add_job(persist_risk_snapshot, "interval", seconds=60)
    scheduler.add_job(persist_metrics_snapshot, "interval", minutes=5)

    scheduler.start()
    
    