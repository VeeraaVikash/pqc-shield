from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id = Column(Integer, primary_key=True, index=True)
    risk_score = Column(Float)
    risk_level = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)