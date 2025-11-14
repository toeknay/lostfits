from sqlalchemy import BigInteger, Column, ForeignKey, String

from app.db import Base


class Constellation(Base):
    __tablename__ = "constellation"
    constellation_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    region_id = Column(BigInteger, ForeignKey("region.region_id"), nullable=False, index=True)
