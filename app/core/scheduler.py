from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from app.services.telemetry_service import generate_tls_handshake, cleanup_stale_sessions
from app.services.alert_service import evaluate_alerts, escalate_alerts
from app.services.risk_service import persist_risk_snapshot
from app.services.inventory_service import seed_inventory, drift_inventory
from app.services.policy_service import seed_policies
from app.services.metrics_service import persist_metrics_snapshot
from app.services.kms_service import auto_rotate_keys, seed_demo_key
from app.services.qos_service import calculate_qos_metrics

# FIX: Limit thread pool — was allowing too many concurrent DB writers
executors = {
    "default": ThreadPoolExecutor(max_workers=4)
}

job_defaults = {
    "coalesce": True,           # FIX: if missed multiple times, only run once
    "max_instances": 1,         # FIX: never run >1 copy of any job at once
    "misfire_grace_time": 15,   # allow up to 15s late before skipping
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)


def start_scheduler():

    # Seed initial data once at startup (not on a schedule)
    seed_inventory()
    seed_policies()
    seed_demo_key()
    auto_rotate_keys()
    calculate_qos_metrics()

    # --- Telemetry ---
    # FIX: Was every 1s with max_instances=5 → caused DB lock storm
    # Now: every 5s, single instance, coalesced
    scheduler.add_job(
        generate_tls_handshake,
        "interval",
        seconds=5,
        id="generate_tls_handshake",
    )

    # FIX: Was every 5s → now every 10s to reduce write pressure
    scheduler.add_job(
        cleanup_stale_sessions,
        "interval",
        seconds=10,
        id="cleanup_stale_sessions",
    )

    # --- Alert monitoring ---
    scheduler.add_job(
        evaluate_alerts,
        "interval",
        seconds=10,
        id="evaluate_alerts",
    )

    # --- Escalation engine ---
    scheduler.add_job(
        escalate_alerts,
        "interval",
        seconds=15,
        id="escalate_alerts",
    )

    # --- Risk snapshot ---
    scheduler.add_job(
        persist_risk_snapshot,
        "interval",
        seconds=60,
        id="persist_risk_snapshot",
    )

    # --- Metrics snapshot ---
    scheduler.add_job(
        persist_metrics_snapshot,
        "interval",
        minutes=5,
        id="persist_metrics_snapshot",
    )

    # --- Key rotation (demo key expires in 45s, check every 15s) ---
    scheduler.add_job(
        auto_rotate_keys,
        "interval",
        seconds=15,
        id="auto_rotate_keys",
    )

    # --- QoS recalculation ---
    scheduler.add_job(
        calculate_qos_metrics,
        "interval",
        seconds=30,
        id="calculate_qos_metrics",
    )

    # --- Inventory drift ---
    scheduler.add_job(
        drift_inventory,
        "interval",
        seconds=30,
        id="drift_inventory",
    )

    scheduler.start()