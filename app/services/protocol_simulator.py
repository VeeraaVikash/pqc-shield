"""
Protocol Simulator — generates realistic real-time data for TLS, SSH, IPsec, VPN.
This runs alongside the existing TLS handshake simulator to provide
unified protocol coverage metrics for the dashboard.
"""
import random
import time
import uuid
from datetime import datetime, timedelta

# ── Protocol State (in-memory, refreshed each call) ──

_REGIONS = ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2"]
_KEM_ALGOS = ["Kyber768", "Kyber1024", "Kyber512"]
_SIG_ALGOS = ["Dilithium3", "Dilithium5", "SPHINCS+-SHA256", "Falcon-512"]
_CLASSICAL = ["RSA-2048", "ECDH-P256", "Ed25519", "AES-256-GCM"]
_MODES = ["PQC-Only", "Hybrid", "Classical"]

_start_time = time.time()


def _uptime():
    mins = int((time.time() - _start_time) / 60)
    if mins < 60:
        return f"{mins}m"
    return f"{mins // 60}h {mins % 60}m"


def get_protocol_overview():
    """Main dashboard endpoint — returns all 4 protocol stats."""
    elapsed = time.time() - _start_time
    base_tls = 1200 + int(elapsed * 0.5) + random.randint(-20, 20)
    base_ssh = 340 + int(elapsed * 0.1) + random.randint(-5, 5)
    base_ipsec = 89 + random.randint(-3, 3)
    base_vpn = 156 + random.randint(-8, 8)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "protocols": {
            "tls": {
                "name": "TLS 1.3 + PQC",
                "status": "operational",
                "active_connections": base_tls,
                "handshakes_per_hour": base_tls * 3 + random.randint(0, 100),
                "pqc_percentage": min(98, 72 + int(elapsed * 0.02)),
                "hybrid_percentage": max(2, 28 - int(elapsed * 0.02)),
                "classical_percentage": 0,
                "avg_latency_ms": round(2.1 + random.uniform(-0.3, 0.3), 1),
                "p99_latency_ms": round(4.2 + random.uniform(-0.5, 0.5), 1),
                "success_rate": round(99.7 + random.uniform(0, 0.29), 2),
                "failure_rate": round(0.01 + random.uniform(0, 0.1), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "endpoints_protected": 847 + random.randint(0, 10),
                "certificates_active": 234,
                "certificates_expiring_30d": random.randint(2, 8),
            },
            "ssh": {
                "name": "SSH + PQC Bastion",
                "status": "operational",
                "active_sessions": base_ssh,
                "auth_per_hour": base_ssh * 2 + random.randint(0, 30),
                "pqc_percentage": min(95, 65 + int(elapsed * 0.015)),
                "hybrid_percentage": max(5, 35 - int(elapsed * 0.015)),
                "classical_percentage": 0,
                "avg_latency_ms": round(1.8 + random.uniform(-0.2, 0.2), 1),
                "p99_latency_ms": round(3.5 + random.uniform(-0.3, 0.3), 1),
                "success_rate": round(99.8 + random.uniform(0, 0.19), 2),
                "failure_rate": round(0.01 + random.uniform(0, 0.08), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "bastions_active": 4,
                "bastions_total": 4,
                "key_exchanges_today": 2840 + random.randint(0, 200),
            },
            "ipsec": {
                "name": "IPsec IKEv2 + PQC",
                "status": "operational",
                "active_tunnels": base_ipsec,
                "sa_negotiations_per_hour": base_ipsec * 4 + random.randint(0, 20),
                "pqc_percentage": min(88, 45 + int(elapsed * 0.025)),
                "hybrid_percentage": min(50, max(12, 55 - int(elapsed * 0.025))),
                "classical_percentage": max(0, 10 - int(elapsed * 0.01)),
                "avg_latency_ms": round(3.4 + random.uniform(-0.4, 0.4), 1),
                "p99_latency_ms": round(7.8 + random.uniform(-0.8, 0.8), 1),
                "success_rate": round(99.5 + random.uniform(0, 0.4), 2),
                "failure_rate": round(0.05 + random.uniform(0, 0.15), 2),
                "primary_kem": "Kyber1024",
                "primary_sig": "Dilithium5",
                "tunnels_pqc": base_ipsec - random.randint(8, 15),
                "tunnels_hybrid": random.randint(5, 12),
                "tunnels_classical": random.randint(0, 3),
                "throughput_gbps": round(12.4 + random.uniform(-1.5, 1.5), 1),
            },
            "vpn": {
                "name": "WireGuard + PQC Overlay",
                "status": "operational",
                "active_peers": base_vpn,
                "connections_per_hour": base_vpn * 2 + random.randint(0, 40),
                "pqc_percentage": min(92, 58 + int(elapsed * 0.02)),
                "hybrid_percentage": max(8, 42 - int(elapsed * 0.02)),
                "classical_percentage": 0,
                "avg_latency_ms": round(1.5 + random.uniform(-0.2, 0.2), 1),
                "p99_latency_ms": round(3.1 + random.uniform(-0.3, 0.3), 1),
                "success_rate": round(99.9 + random.uniform(0, 0.09), 2),
                "failure_rate": round(0.01 + random.uniform(0, 0.05), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "roaming_clients": random.randint(30, 60),
                "site_to_site": random.randint(12, 20),
                "throughput_gbps": round(8.7 + random.uniform(-1, 1), 1),
            },
        },
        "summary": {
            "total_connections": base_tls + base_ssh + base_ipsec + base_vpn,
            "overall_pqc_coverage": round(
                (min(98, 72 + int(elapsed * 0.02)) * base_tls +
                 min(95, 65 + int(elapsed * 0.015)) * base_ssh +
                 min(88, 45 + int(elapsed * 0.025)) * base_ipsec +
                 min(92, 58 + int(elapsed * 0.02)) * base_vpn) /
                max(1, base_tls + base_ssh + base_ipsec + base_vpn), 1
            ),
            "protocols_operational": 4,
            "protocols_total": 4,
            "uptime": _uptime(),
            "migration_phase": "Phase 2 — Hybrid Rollout",
            "cnsa_2_0_target": "2030-12-31",
            "days_to_target": (datetime(2030, 12, 31) - datetime.utcnow()).days,
        },
        "algorithm_distribution": _get_algo_distribution(elapsed),
        "migration_timeline": _get_migration_timeline(),
    }


def _get_algo_distribution(elapsed):
    kyber768 = min(52, 35 + int(elapsed * 0.01))
    kyber1024 = min(18, 10 + int(elapsed * 0.005))
    dilithium3 = min(15, 10 + int(elapsed * 0.003))
    hybrid = max(10, 30 - int(elapsed * 0.015))
    classical = max(5, 15 - int(elapsed * 0.008))
    return {
        "Kyber768": kyber768,
        "Kyber1024": kyber1024,
        "Dilithium3": dilithium3,
        "Hybrid (ECDH+Kyber)": hybrid,
        "Classical": classical,
    }


def _get_migration_timeline():
    return [
        {"phase": "Assessment", "status": "completed", "target": "2024-Q4", "progress": 100},
        {"phase": "Pilot (TLS)", "status": "completed", "target": "2025-Q1", "progress": 100},
        {"phase": "Hybrid Rollout", "status": "in_progress", "target": "2025-Q3", "progress": 68},
        {"phase": "Full PQC (TLS/SSH)", "status": "planned", "target": "2026-Q1", "progress": 0},
        {"phase": "IPsec Migration", "status": "planned", "target": "2026-Q3", "progress": 0},
        {"phase": "CNSA 2.0 Compliance", "status": "planned", "target": "2030-Q4", "progress": 0},
    ]


def get_active_vpn_peers():
    """Returns list of active VPN peers with details."""
    peers = []
    for i in range(random.randint(12, 20)):
        mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[60, 35, 5])[0]
        peers.append({
            "peer_id": f"vpn-{uuid.uuid4().hex[:8]}",
            "endpoint": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}:{random.randint(40000,60000)}",
            "tunnel_ip": f"172.16.{random.randint(0,15)}.{random.randint(1,254)}",
            "kem": random.choice(_KEM_ALGOS) if mode != "Classical" else "ECDH-P256",
            "signature": random.choice(_SIG_ALGOS) if mode != "Classical" else "Ed25519",
            "mode": mode,
            "rx_bytes": f"{random.randint(100, 9999)} MB",
            "tx_bytes": f"{random.randint(50, 5000)} MB",
            "uptime": f"{random.randint(1, 72)}h",
            "last_handshake": f"{random.randint(1, 120)}s ago",
            "status": random.choices(["active", "idle"], weights=[85, 15])[0],
        })
    return peers


def get_ipsec_tunnels():
    """Returns list of active IPsec tunnels."""
    sites = [
        ("HQ-DC1", "Branch-NYC"), ("HQ-DC1", "Branch-LON"), ("HQ-DC1", "Branch-SIN"),
        ("HQ-DC2", "Branch-TYO"), ("HQ-DC2", "Branch-SYD"), ("DR-Site", "HQ-DC1"),
        ("Branch-NYC", "Branch-LON"), ("Cloud-AWS", "HQ-DC1"), ("Cloud-GCP", "HQ-DC2"),
    ]
    tunnels = []
    for src, dst in sites:
        mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[50, 40, 10])[0]
        tunnels.append({
            "tunnel_id": f"ipsec-{uuid.uuid4().hex[:8]}",
            "source": src,
            "destination": dst,
            "ike_version": "IKEv2",
            "kem": random.choice(["Kyber1024", "Kyber768"]) if mode != "Classical" else "DH-Group20",
            "auth": random.choice(["Dilithium5", "Dilithium3"]) if mode != "Classical" else "RSA-2048",
            "esp_cipher": "AES-256-GCM",
            "mode": mode,
            "sa_lifetime": f"{random.randint(1, 8)}h remaining",
            "bytes_transferred": f"{random.randint(10, 500)} GB",
            "status": random.choices(["established", "rekeying"], weights=[90, 10])[0],
        })
    return tunnels
