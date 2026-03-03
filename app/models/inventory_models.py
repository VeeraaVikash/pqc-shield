from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
import uuid
from app.database import Base


class InventoryAsset(Base):
    __tablename__ = "inventory_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hostname = Column(String, nullable=False)
    asset_type = Column(String)  # TLS Gateway / Bastion / App Server / LB
    algorithm = Column(String)
    status = Column(String)  # active / warning / inactive
    cert_expiry = Column(DateTime)
    pqc_readiness = Column(Integer)  # 0–100 percentage
    last_updated = Column(DateTime, default=datetime.utcnow)