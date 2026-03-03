from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String)
    actor = Column(String)  # system / admin / scheduler
    source = Column(String)  # module name

    description = Column(String)
    severity = Column(String)  # INFO / WARNING / CRITICAL

    timestamp = Column(DateTime, default=datetime.utcnow)