"""
SSH Bastion Simulator — generates STABLE SSH session data.
Uses persistent state so numbers don't jump randomly between API calls.
"""
import random
import math
import uuid
import time
from datetime import datetime, timedelta

_start_time = time.time()

# Fixed bastion hosts (represent real infrastructure)
_BASTIONS = [
    {"id": "BASTION-01", "host": "ssh-gw-east.pqc-vault.io", "region": "us-east-1", "ip": "10.0.1.50"},
    {"id": "BASTION-02", "host": "ssh-gw-west.pqc-vault.io", "region": "us-west-2", "ip": "10.0.2.50"},
    {"id": "BASTION-03", "host": "ssh-gw-eu.pqc-vault.io", "region": "eu-west-1", "ip": "10.0.3.50"},
    {"id": "BASTION-04", "host": "ssh-gw-asia.pqc-vault.io", "region": "ap-south-1", "ip": "10.0.4.50"},
]

_USERS = ["admin", "devops", "sre-team", "deploy-bot", "audit-svc", "k8s-admin", "db-admin", "ci-runner"]
_TARGETS = [
    "prod-web-01", "prod-web-02", "prod-db-master", "prod-db-replica",
    "staging-api-01", "k8s-master-01", "k8s-worker-03", "monitoring-01",
    "vault-server", "ci-runner-02", "log-aggregator", "backup-server",
]
_ALGOS = ["Dilithium3", "Dilithium5", "SPHINCS+-SHA256", "Falcon-512"]
_KEM_ALGOS = ["Kyber768", "Kyber1024"]

# ── Persistent bastion state ──
_bastion_state = None
_session_state = None
_session_last_refresh = 0


def _init_bastion_state():
    global _bastion_state
    _bastion_state = []
    for b in _BASTIONS:
        _bastion_state.append({
            **b,
            "sessions": random.randint(15, 35),
            "auth_algo": random.choice(["Dilithium3", "Dilithium5"]),
            "kex_algo": random.choice(["Kyber768", "Kyber1024"]),
            "mode": random.choices(["PQC-Only", "Hybrid"], weights=[70, 30])[0],
            "cpu": random.uniform(20, 50),
            "memory": random.uniform(40, 65),
            "failed_24h": random.randint(1, 8),
            "kex_today": random.randint(400, 600),
        })


def get_ssh_bastions():
    """Returns list of SSH bastion hosts with slowly drifting metrics."""
    global _bastion_state
    if _bastion_state is None:
        _init_bastion_state()

    elapsed = time.time() - _start_time

    bastions = []
    for bs in _bastion_state:
        # Slow drift
        bs["sessions"] = max(8, min(50, bs["sessions"] + random.uniform(-0.5, 0.7)))
        bs["cpu"] = max(10, min(80, bs["cpu"] + random.uniform(-0.3, 0.3)))
        bs["memory"] = max(25, min(85, bs["memory"] + random.uniform(-0.2, 0.2)))
        bs["kex_today"] += random.randint(0, 2)

        uptime_hours = int(elapsed / 3600) + 240

        bastions.append({
            "id": bs["id"],
            "host": bs["host"],
            "ip": bs["ip"],
            "region": bs["region"],
            "status": "active",
            "active_sessions": int(bs["sessions"]),
            "auth_algorithm": bs["auth_algo"],
            "kex_algorithm": bs["kex_algo"],
            "mode": bs["mode"],
            "uptime": f"{uptime_hours}h",
            "cpu_usage": round(bs["cpu"], 1),
            "memory_usage": round(bs["memory"], 1),
            "auth_success_rate": round(99.5 + 0.3 * math.sin(elapsed * 0.02), 2),
            "failed_attempts_24h": bs["failed_24h"],
            "key_exchanges_today": bs["kex_today"],
            "last_key_rotation": "3d ago",
            "firmware_version": "PQC-SSH-2.1.4",
            "pqc_percentage": min(95, 65 + int(elapsed * 0.015)),
        })

    return bastions


def get_ssh_sessions():
    """Returns a STABLE list of SSH sessions that evolves slowly."""
    global _session_state, _session_last_refresh
    now = time.time()

    # Only regenerate sessions every 30 seconds (not every API call)
    if _session_state is None or (now - _session_last_refresh) > 30:
        _session_state = []
        num_sessions = random.randint(25, 40)

        for i in range(num_sessions):
            bastion = _BASTIONS[i % len(_BASTIONS)]
            user = _USERS[i % len(_USERS)]
            target = _TARGETS[i % len(_TARGETS)]
            algo = _ALGOS[i % len(_ALGOS)]
            kem = _KEM_ALGOS[i % len(_KEM_ALGOS)]
            mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[65, 30, 5])[0]

            duration_min = random.randint(5, 300)

            _session_state.append({
                "session_id": f"ssh-{uuid.uuid4().hex[:8]}",
                "user": user,
                "bastion": bastion["id"],
                "bastion_region": bastion["region"],
                "target": target,
                "target_ip": f"10.{10 + i}.{random.randint(1,254)}.{random.randint(1,254)}",
                "auth_algorithm": algo if mode != "Classical" else "Ed25519",
                "kex_algorithm": kem if mode != "Classical" else "ECDH-P256",
                "mode": mode,
                "cipher": "AES-256-GCM",
                "_duration": duration_min,
                "bytes_transferred": f"{random.randint(5, 200)} MB",
                "commands_executed": random.randint(5, 100),
                "status": random.choices(["active", "idle"], weights=[80, 20])[0],
                "started_at": (datetime.utcnow() - timedelta(minutes=duration_min)).isoformat(),
            })

        _session_last_refresh = now
    else:
        # Just increment durations and commands
        for s in _session_state:
            s["_duration"] += 1
            s["commands_executed"] += random.randint(0, 2)

    # Format duration for output
    result = []
    for s in _session_state:
        d = s["_duration"]
        dur = f"{d}m" if d < 60 else f"{d // 60}h {d % 60}m"
        entry = {k: v for k, v in s.items() if not k.startswith("_")}
        entry["duration"] = dur
        result.append(entry)

    return result


def get_ssh_metrics():
    """Returns aggregated SSH metrics."""
    elapsed = time.time() - _start_time
    bastions = get_ssh_bastions()
    total_sessions = sum(b["active_sessions"] for b in bastions)

    return {
        "total_bastions": len(bastions),
        "bastions_active": sum(1 for b in bastions if b["status"] == "active"),
        "bastions_maintenance": sum(1 for b in bastions if b["status"] == "maintenance"),
        "total_active_sessions": total_sessions,
        "total_auth_today": sum(b["key_exchanges_today"] for b in bastions),
        "pqc_percentage": min(95, 65 + int(elapsed * 0.015)),
        "hybrid_percentage": max(5, 35 - int(elapsed * 0.015)),
        "classical_percentage": 0,
        "avg_auth_latency_ms": round(1.8 + 0.1 * math.sin(elapsed * 0.03), 1),
        "failed_attempts_24h": sum(b["failed_attempts_24h"] for b in bastions),
        "primary_auth_algo": "Dilithium3",
        "primary_kex_algo": "Kyber768",
    }
