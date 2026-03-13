"""
Protocol Simulator — generates STABLE real-time data for TLS, SSH, IPsec, VPN.
Uses slow drift instead of random jumps so numbers look realistic during demos.
"""
import random
import math
import time
import uuid
from datetime import datetime, timedelta

_REGIONS = ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2"]
_KEM_ALGOS = ["Kyber768", "Kyber1024", "Kyber512"]
_SIG_ALGOS = ["Dilithium3", "Dilithium5", "SPHINCS+-SHA256", "Falcon-512"]
_CLASSICAL = ["RSA-2048", "ECDH-P256", "Ed25519", "AES-256-GCM"]

_start_time = time.time()

# ── Stable state that drifts slowly ──
_state = {
    "tls_conns": 1200,
    "ssh_sessions": 340,
    "ipsec_tunnels": 89,
    "vpn_peers": 156,
    "last_drift": 0,
}


def _drift(current, target_min, target_max, speed=0.3):
    """Slowly drift a number toward a target range. No sudden jumps."""
    target = (target_min + target_max) / 2
    diff = target - current
    nudge = diff * speed * 0.1 + random.uniform(-1, 1)
    return max(target_min * 0.9, min(target_max * 1.1, current + nudge))


def _smooth_latency(base, amplitude=0.2):
    """Use sine wave for smooth latency so it doesn't jump randomly."""
    t = time.time() - _start_time
    return round(base + amplitude * math.sin(t * 0.1) + random.uniform(-0.05, 0.05), 1)


def _uptime():
    mins = int((time.time() - _start_time) / 60)
    if mins < 60:
        return f"{mins}m"
    return f"{mins // 60}h {mins % 60}m"


def _update_state():
    """Drift state every call — slow, smooth transitions."""
    now = time.time()
    elapsed = now - _start_time

    _state["tls_conns"] = _drift(_state["tls_conns"], 1100 + elapsed * 0.3, 1400 + elapsed * 0.5)
    _state["ssh_sessions"] = _drift(_state["ssh_sessions"], 320, 380)
    _state["ipsec_tunnels"] = _drift(_state["ipsec_tunnels"], 82, 96)
    _state["vpn_peers"] = _drift(_state["vpn_peers"], 145, 170)
    _state["last_drift"] = now


def get_protocol_overview():
    """Main dashboard endpoint — returns all 4 protocol stats with smooth drift."""
    _update_state()
    elapsed = time.time() - _start_time

    base_tls = int(_state["tls_conns"])
    base_ssh = int(_state["ssh_sessions"])
    base_ipsec = int(_state["ipsec_tunnels"])
    base_vpn = int(_state["vpn_peers"])

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "protocols": {
            "tls": {
                "name": "TLS 1.3 + PQC",
                "status": "operational",
                "active_connections": base_tls,
                "handshakes_per_hour": base_tls * 3 + int(math.sin(elapsed * 0.05) * 30),
                "pqc_percentage": min(98, 72 + int(elapsed * 0.02)),
                "hybrid_percentage": max(2, 28 - int(elapsed * 0.02)),
                "classical_percentage": 0,
                "avg_latency_ms": _smooth_latency(2.1),
                "p99_latency_ms": _smooth_latency(4.2, 0.3),
                "success_rate": round(99.7 + 0.15 * math.sin(elapsed * 0.02), 2),
                "failure_rate": round(0.05 + 0.03 * math.sin(elapsed * 0.03), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "endpoints_protected": 847 + int(elapsed * 0.01),
                "certificates_active": 234,
                "certificates_expiring_30d": 4,
            },
            "ssh": {
                "name": "SSH + PQC Bastion",
                "status": "operational",
                "active_sessions": base_ssh,
                "auth_per_hour": base_ssh * 2 + int(math.sin(elapsed * 0.04) * 10),
                "pqc_percentage": min(95, 65 + int(elapsed * 0.015)),
                "hybrid_percentage": max(5, 35 - int(elapsed * 0.015)),
                "classical_percentage": 0,
                "avg_latency_ms": _smooth_latency(1.8, 0.15),
                "p99_latency_ms": _smooth_latency(3.5, 0.2),
                "success_rate": round(99.8 + 0.1 * math.sin(elapsed * 0.025), 2),
                "failure_rate": round(0.03 + 0.02 * math.sin(elapsed * 0.035), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "bastions_active": 4,
                "bastions_total": 4,
                "key_exchanges_today": 2840 + int(elapsed * 0.5),
            },
            "ipsec": {
                "name": "IPsec IKEv2 + PQC",
                "status": "operational",
                "active_tunnels": base_ipsec,
                "sa_negotiations_per_hour": base_ipsec * 4 + int(math.sin(elapsed * 0.06) * 8),
                "pqc_percentage": min(88, 45 + int(elapsed * 0.025)),
                "hybrid_percentage": min(50, max(12, 55 - int(elapsed * 0.025))),
                "classical_percentage": max(0, 10 - int(elapsed * 0.01)),
                "avg_latency_ms": _smooth_latency(3.4, 0.3),
                "p99_latency_ms": _smooth_latency(7.8, 0.5),
                "success_rate": round(99.5 + 0.2 * math.sin(elapsed * 0.03), 2),
                "failure_rate": round(0.08 + 0.05 * math.sin(elapsed * 0.04), 2),
                "primary_kem": "Kyber1024",
                "primary_sig": "Dilithium5",
                "tunnels_pqc": max(0, base_ipsec - 18),
                "tunnels_hybrid": 12,
                "tunnels_classical": max(0, min(6, base_ipsec - (base_ipsec - 18) - 12)),
                "throughput_gbps": round(12.4 + 1.0 * math.sin(elapsed * 0.02), 1),
            },
            "vpn": {
                "name": "WireGuard + PQC Overlay",
                "status": "operational",
                "active_peers": base_vpn,
                "connections_per_hour": base_vpn * 2 + int(math.sin(elapsed * 0.07) * 12),
                "pqc_percentage": min(92, 58 + int(elapsed * 0.02)),
                "hybrid_percentage": max(8, 42 - int(elapsed * 0.02)),
                "classical_percentage": 0,
                "avg_latency_ms": _smooth_latency(1.5, 0.1),
                "p99_latency_ms": _smooth_latency(3.1, 0.2),
                "success_rate": round(99.9 + 0.05 * math.sin(elapsed * 0.02), 2),
                "failure_rate": round(0.02 + 0.01 * math.sin(elapsed * 0.04), 2),
                "primary_kem": "Kyber768",
                "primary_sig": "Dilithium3",
                "roaming_clients": int(base_vpn * 0.35),
                "site_to_site": int(base_vpn * 0.1),
                "throughput_gbps": round(8.7 + 0.6 * math.sin(elapsed * 0.03), 1),
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


# ── Stable VPN peers (fixed list, not regenerated each call) ──
_vpn_peers = None

def get_active_vpn_peers():
    """Returns a STABLE list of VPN peers that drifts slowly."""
    global _vpn_peers
    if _vpn_peers is None:
        _vpn_peers = []
        for i in range(15):
            mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[60, 35, 5])[0]
            _vpn_peers.append({
                "peer_id": f"vpn-peer-{i+1:02d}",
                "endpoint": f"10.{50+i}.{random.randint(1,254)}.{random.randint(1,254)}:{51820+i}",
                "tunnel_ip": f"172.16.{i//4}.{i*16+1}",
                "kem": random.choice(_KEM_ALGOS) if mode != "Classical" else "ECDH-P256",
                "signature": random.choice(_SIG_ALGOS) if mode != "Classical" else "Ed25519",
                "mode": mode,
                "_rx_base": random.randint(100, 5000),
                "_tx_base": random.randint(50, 3000),
                "uptime": f"{random.randint(1, 72)}h",
                "status": random.choices(["active", "idle"], weights=[85, 15])[0],
            })

    # Slowly increment traffic counters
    for p in _vpn_peers:
        p["_rx_base"] += random.randint(0, 5)
        p["_tx_base"] += random.randint(0, 3)
        p["rx_bytes"] = f"{p['_rx_base']} MB"
        p["tx_bytes"] = f"{p['_tx_base']} MB"
        p["last_handshake"] = f"{random.randint(1, 30)}s ago"

    return [{k: v for k, v in p.items() if not k.startswith("_")} for p in _vpn_peers]


# ── Stable IPsec tunnels (fixed list) ──
_ipsec_tunnels = None

def get_ipsec_tunnels():
    """Returns a STABLE list of IPsec tunnels."""
    global _ipsec_tunnels
    if _ipsec_tunnels is None:
        sites = [
            ("HQ-DC1", "Branch-NYC"), ("HQ-DC1", "Branch-LON"), ("HQ-DC1", "Branch-SIN"),
            ("HQ-DC2", "Branch-TYO"), ("HQ-DC2", "Branch-SYD"), ("DR-Site", "HQ-DC1"),
            ("Branch-NYC", "Branch-LON"), ("Cloud-AWS", "HQ-DC1"), ("Cloud-GCP", "HQ-DC2"),
        ]
        _ipsec_tunnels = []
        for i, (src, dst) in enumerate(sites):
            mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[50, 40, 10])[0]
            _ipsec_tunnels.append({
                "tunnel_id": f"ipsec-tun-{i+1:02d}",
                "source": src,
                "destination": dst,
                "ike_version": "IKEv2",
                "kem": random.choice(["Kyber1024", "Kyber768"]) if mode != "Classical" else "DH-Group20",
                "auth": random.choice(["Dilithium5", "Dilithium3"]) if mode != "Classical" else "RSA-2048",
                "esp_cipher": "AES-256-GCM",
                "mode": mode,
                "_sa_hours": random.uniform(1, 8),
                "_gb_base": random.randint(10, 500),
                "status": "established",
            })

    # Slowly drift values
    for t in _ipsec_tunnels:
        t["_sa_hours"] = max(0.1, t["_sa_hours"] - 0.002)
        if t["_sa_hours"] < 0.5:
            t["_sa_hours"] = random.uniform(6, 8)
            t["status"] = "rekeying"
        else:
            t["status"] = "established"
        t["_gb_base"] += random.randint(0, 2)
        t["sa_lifetime"] = f"{t['_sa_hours']:.1f}h remaining"
        t["bytes_transferred"] = f"{t['_gb_base']} GB"

    return [{k: v for k, v in t.items() if not k.startswith("_")} for t in _ipsec_tunnels]
