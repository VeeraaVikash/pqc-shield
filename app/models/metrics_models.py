from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    handshakes_per_hour = Column(Integer)
    avg_latency = Column(Float)
    success_rate = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())