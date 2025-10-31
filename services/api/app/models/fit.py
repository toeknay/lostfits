from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.sql import func
from app.db import Base

class Fit(Base):
    __tablename__ = "fit"
    fit_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    killmail_id = Column(BigInteger, ForeignKey("killmail_raw.killmail_id"), nullable=False, index=True)
    ship_type_id = Column(BigInteger, nullable=False, index=True)
    fit_signature = Column(String(128), nullable=False, index=True)
    slot_counts = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
