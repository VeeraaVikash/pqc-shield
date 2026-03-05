from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake, ActiveTLSConnection
from app.models.inventory_models import InventoryAsset
from app.models.key_models import Key
from app.models.alert_models import Alert
from app.services.telemetry_service import get_performance_metrics
from app.services.protocol_simulator import get_protocol_overview

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    """Prometheus-compatible /metrics endpoint for Grafana/SIEM."""
    db = SessionLocal()
    now = datetime.utcnow()
    one_hour = now - timedelta(hours=1)

    total_hs = db.query(TLSHandshake).filter(TLSHandshake.timestamp > one_hour).count()
    failed_hs = db.query(TLSHandshake).filter(TLSHandshake.timestamp > one_hour, TLSHandshake.success == False).count()
    fallback_hs = db.query(TLSHandshake).filter(TLSHandshake.timestamp > one_hour, TLSHandshake.fallback_triggered == True).count()
    active_conns = db.query(ActiveTLSConnection).filter(ActiveTLSConnection.status == "active").count()
    total_assets = db.query(InventoryAsset).count()
    pqc_ready = db.query(InventoryAsset).filter(InventoryAsset.pqc_readiness >= 85).count()
    total_keys = db.query(Key).count()
    pqc_keys = db.query(Key).filter(~Key.algorithm.contains("RSA")).count()
    expiring_keys = db.query(Key).filter(Key.expires_at < now + timedelta(days=30)).count()
    open_alerts = db.query(Alert).filter(Alert.status == "OPEN").count()
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL", Alert.status == "OPEN").count()
    db.close()

    perf = get_performance_metrics()
    proto = get_protocol_overview()
    summary = proto.get("summary", {})

    lines = [
        '# HELP pqc_shield_info PQC Shield platform info',
        '# TYPE pqc_shield_info gauge',
        'pqc_shield_info{version="1.0.0"} 1',
        '',
        '# HELP pqc_tls_handshakes_total TLS handshakes in last hour',
        '# TYPE pqc_tls_handshakes_total gauge',
        f'pqc_tls_handshakes_total {total_hs}',
        '',
        '# HELP pqc_tls_handshakes_failed Failed TLS handshakes',
        '# TYPE pqc_tls_handshakes_failed gauge',
        f'pqc_tls_handshakes_failed {failed_hs}',
        '',
        '# HELP pqc_tls_fallbacks_total Fallback handshakes',
        '# TYPE pqc_tls_fallbacks_total gauge',
        f'pqc_tls_fallbacks_total {fallback_hs}',
        '',
        '# HELP pqc_tls_active_connections Active TLS connections',
        '# TYPE pqc_tls_active_connections gauge',
        f'pqc_tls_active_connections {active_conns}',
        '',
        '# HELP pqc_tls_latency_p50_ms P50 latency',
        '# TYPE pqc_tls_latency_p50_ms gauge',
        f'pqc_tls_latency_p50_ms {perf.get("p50_latency", 0)}',
        '',
        '# HELP pqc_tls_latency_p99_ms P99 latency',
        '# TYPE pqc_tls_latency_p99_ms gauge',
        f'pqc_tls_latency_p99_ms {perf.get("p99_latency", 0)}',
        '',
        '# HELP pqc_tls_success_rate Success rate',
        '# TYPE pqc_tls_success_rate gauge',
        f'pqc_tls_success_rate {perf.get("success_rate", 0)}',
        '',
        '# HELP pqc_assets_total Total assets',
        '# TYPE pqc_assets_total gauge',
        f'pqc_assets_total {total_assets}',
        '',
        '# HELP pqc_assets_pqc_ready PQC ready assets',
        '# TYPE pqc_assets_pqc_ready gauge',
        f'pqc_assets_pqc_ready {pqc_ready}',
        '',
        '# HELP pqc_keys_total Total keys',
        '# TYPE pqc_keys_total gauge',
        f'pqc_keys_total {total_keys}',
        '',
        '# HELP pqc_keys_pqc PQC keys',
        '# TYPE pqc_keys_pqc gauge',
        f'pqc_keys_pqc {pqc_keys}',
        '',
        '# HELP pqc_keys_expiring Expiring keys',
        '# TYPE pqc_keys_expiring gauge',
        f'pqc_keys_expiring {expiring_keys}',
        '',
        '# HELP pqc_alerts_open Open alerts',
        '# TYPE pqc_alerts_open gauge',
        f'pqc_alerts_open {open_alerts}',
        '',
        '# HELP pqc_alerts_critical Critical alerts',
        '# TYPE pqc_alerts_critical gauge',
        f'pqc_alerts_critical {critical_alerts}',
        '',
        '# HELP pqc_protocols_operational Operational protocols',
        '# TYPE pqc_protocols_operational gauge',
        f'pqc_protocols_operational {summary.get("protocols_operational", 4)}',
        '',
        '# HELP pqc_coverage_overall Overall PQC coverage',
        '# TYPE pqc_coverage_overall gauge',
        f'pqc_coverage_overall {summary.get("overall_pqc_coverage", 0)}',
        '',
        '# HELP pqc_connections_total Total connections all protocols',
        '# TYPE pqc_connections_total gauge',
        f'pqc_connections_total {summary.get("total_connections", 0)}',
    ]

    return "\n".join(lines) + "\n"