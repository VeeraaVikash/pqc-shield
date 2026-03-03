from sqlalchemy import Column, String, Integer, Boolean, DateTime
from datetime import datetime
import uuid
from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True)
    target_group = Column(String)  # TLS Gateway / SSH Bastion / etc

    required_kem = Column(String)
    required_signature = Column(String)

    enforcement = Column(String)  # STRICT / WARNING
    rollout_strategy = Column(String)  # GLOBAL / CANARY
    canary_percentage = Column(Integer, default=100)

    fallback_allowed = Column(Boolean, default=True)
    sunset_date = Column(DateTime)

    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)