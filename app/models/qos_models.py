from sqlalchemy import Column, Integer, Float, String, DateTime
from app.database import Base
from datetime import datetime


class QoSMetrics(Base):
    __tablename__ = "qos_metrics"

    id = Column(Integer, primary_key=True, index=True)

    availability_30d = Column(Float)   # %
    mttr_seconds = Column(Float)
    failed_handshakes_24h = Column(Integer)

    fallback_triggers_24h = Column(Integer)
    replay_attacks_detected = Column(Integer)

    status = Column(String, default="HEALTHY")

    timestamp = Column(DateTime, default=datetime.utcnow)