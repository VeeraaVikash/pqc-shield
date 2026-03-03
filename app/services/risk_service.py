from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.tls_models import TLSHandshake
from app.services.policy_service import calculate_policy_coverage
from app.models.risk_models import RiskHistory


def calculate_risk_score():
    db = SessionLocal()

    # ---- POLICY COVERAGE ----
    coverage_data = calculate_policy_coverage("pqc-tls-mandate")
    coverage = coverage_data.get("coverage_percent", 0)
    coverage_risk = 100 - coverage

    # ---- LAST 1 HOUR HANDSHAKES ----
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    handshakes = db.query(TLSHandshake)\
        .filter(TLSHandshake.timestamp > one_hour_ago)\
        .all()

    total = len(handshakes)

    if total == 0:
        db.close()
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "factors": {}
        }

    failures = len([h for h in handshakes if not h.success])
    failure_rate = failures / total * 100

    classic = len([h for h in handshakes if h.kem_algorithm == "Classic"])
    fallback_rate = classic / total * 100

    latencies = sorted([h.latency_ms for h in handshakes])
    p99_latency = latencies[int(len(latencies) * 0.99)]

    db.close()

    # ---- RISK CALCULATION ----
    risk_score = (
        coverage_risk * 0.4 +
        fallback_rate * 0.25 +
        failure_rate * 0.2 +
        min(p99_latency * 5, 100) * 0.15
    )

    risk_score = round(min(risk_score, 100), 2)

    # ---- RISK LEVEL ----
    if risk_score < 30:
        level = "LOW"
    elif risk_score < 70:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "factors": {
            "policy_coverage": coverage,
            "failure_rate": round(failure_rate, 2),
            "fallback_rate": round(fallback_rate, 2),
            "p99_latency": round(p99_latency, 2)
        }
    }


# ✅ THIS FUNCTION MUST BE OUTSIDE calculate_risk_score
def persist_risk_snapshot():
    db = SessionLocal()

    data = calculate_risk_score()

    record = RiskHistory(
        risk_score=data["risk_score"],
        risk_level=data["risk_level"]
    )

    db.add(record)
    db.commit()
    db.close()