"""
SSH Bastion Simulator — generates realistic SSH session data.
Replaces all frontend mock SSH_BASTIONS and SSH_SESSIONS constants.
Runs in-memory, refreshes each API call with slight variations.
"""
import random
import uuid
import time
from datetime import datetime, timedelta

_start_time = time.time()

# Fixed bastion hosts (these represent real infrastructure)
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


def get_ssh_bastions():
    """Returns list of SSH bastion hosts with real-time metrics."""
    elapsed = time.time() - _start_time
    bastions = []

    for b in _BASTIONS:
        sessions = random.randint(8, 45)
        algo = random.choice(_ALGOS)
        kem = random.choice(_KEM_ALGOS)
        uptime_hours = int(elapsed / 3600) + random.randint(100, 500)

        bastions.append({
            "id": b["id"],
            "host": b["host"],
            "ip": b["ip"],
            "region": b["region"],
            "status": random.choices(["active", "maintenance"], weights=[95, 5])[0],
            "active_sessions": sessions,
            "auth_algorithm": algo,
            "kex_algorithm": kem,
            "mode": random.choices(["PQC-Only", "Hybrid"], weights=[70, 30])[0],
            "uptime": f"{uptime_hours}h",
            "cpu_usage": round(random.uniform(12, 65), 1),
            "memory_usage": round(random.uniform(30, 78), 1),
            "auth_success_rate": round(99.5 + random.uniform(0, 0.49), 2),
            "failed_attempts_24h": random.randint(0, 15),
            "key_exchanges_today": random.randint(200, 800),
            "last_key_rotation": f"{random.randint(1, 14)}d ago",
            "firmware_version": "PQC-SSH-2.1.4",
            "pqc_percentage": min(95, 65 + int(elapsed * 0.015)),
        })

    return bastions


def get_ssh_sessions():
    """Returns list of active SSH sessions across all bastions."""
    sessions = []
    num_sessions = random.randint(20, 50)

    for _ in range(num_sessions):
        bastion = random.choice(_BASTIONS)
        user = random.choice(_USERS)
        target = random.choice(_TARGETS)
        algo = random.choice(_ALGOS)
        kem = random.choice(_KEM_ALGOS)
        mode = random.choices(["PQC-Only", "Hybrid", "Classical"], weights=[65, 30, 5])[0]

        duration_min = random.randint(1, 480)
        if duration_min < 60:
            duration_str = f"{duration_min}m"
        else:
            duration_str = f"{duration_min // 60}h {duration_min % 60}m"

        sessions.append({
            "session_id": f"ssh-{uuid.uuid4().hex[:8]}",
            "user": user,
            "bastion": bastion["id"],
            "bastion_region": bastion["region"],
            "target": target,
            "target_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "auth_algorithm": algo if mode != "Classical" else "Ed25519",
            "kex_algorithm": kem if mode != "Classical" else "ECDH-P256",
            "mode": mode,
            "cipher": "AES-256-GCM",
            "duration": duration_str,
            "bytes_transferred": f"{random.randint(1, 500)} MB",
            "commands_executed": random.randint(1, 200),
            "status": random.choices(["active", "idle"], weights=[80, 20])[0],
            "started_at": (datetime.utcnow() - timedelta(minutes=duration_min)).isoformat(),
        })

    return sessions


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
        "avg_auth_latency_ms": round(1.8 + random.uniform(-0.2, 0.2), 1),
        "failed_attempts_24h": sum(b["failed_attempts_24h"] for b in bastions),
        "primary_auth_algo": "Dilithium3",
        "primary_kex_algo": "Kyber768",
    }
