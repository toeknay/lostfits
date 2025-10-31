from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class FitAggregateDaily(Base):
    __tablename__ = "fit_aggregate_daily"
    date = Column(Date, primary_key=True)
    ship_type_id = Column(BigInteger, primary_key=True)
    fit_signature = Column(String(128), primary_key=True)
    loss_count = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("date", "ship_type_id", "fit_signature", name="uq_daily_agg"),
    )
