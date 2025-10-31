from sqlalchemy import BigInteger, Column, DateTime, JSON, String
from sqlalchemy.sql import func
from app.db import Base

class KillmailRaw(Base):
    __tablename__ = "killmail_raw"
    killmail_id = Column(BigInteger, primary_key=True, index=True)
    killmail_hash = Column(String(64), nullable=False, index=True)
    kill_time = Column(DateTime(timezone=True), nullable=True)
    solar_system_id = Column(BigInteger, nullable=True)
    victim_ship_type_id = Column(BigInteger, nullable=True)
    json = Column(JSON, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
