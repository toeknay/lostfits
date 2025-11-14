from sqlalchemy import BigInteger, Column, ForeignKey, String

from app.db import Base


class SolarSystem(Base):
    __tablename__ = "solar_system"
    system_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    constellation_id = Column(
        BigInteger, ForeignKey("constellation.constellation_id"), nullable=False, index=True
    )
