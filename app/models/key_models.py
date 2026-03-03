from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, index=True)

    key_type = Column(String)  # KEM / SIG
    algorithm = Column(String)
    usage = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    rotation_count = Column(Integer, default=0)
    auto_rotate = Column(Boolean, default=True)

    status = Column(String, default="active")  # active / warning / expired / deprecated

    # Hierarchy simulation
    parent_key_id = Column(Integer, ForeignKey("keys.id"), nullable=True)
    parent_key = relationship("Key", remote_side=[id])


class KeyRotationHistory(Base):
    __tablename__ = "key_rotation_history"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String)
    rotated_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String)