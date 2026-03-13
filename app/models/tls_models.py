from sqlalchemy import Column, String, Float, Boolean, DateTime
from datetime import datetime
import uuid
from app.database import Base


# ---------------------------
# TLS Handshake History Model
# ---------------------------

class TLSHandshake(Base):
    __tablename__ = "tls_handshakes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id = Column(String, nullable=False)
    kem_algorithm = Column(String, nullable=False)
    signature_algorithm = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)
    success = Column(Boolean, default=True)
    fallback_triggered = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ---------------------------
# Active TLS Session Registry
# ---------------------------

class ActiveTLSConnection(Base):
    __tablename__ = "active_tls_connections"
    __mapper_args__ = {"confirm_deleted_rows": False}

    id = Column(String, primary_key=True)
    source = Column(String)
    destination = Column(String)
    kem_algorithm = Column(String)
    signature_algorithm = Column(String)
    mode = Column(String)
    latency_ms = Column(Float)
    status = Column(String, default="active")
    last_seen = Column(DateTime, default=datetime.utcnow)