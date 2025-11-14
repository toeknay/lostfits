from sqlalchemy import BigInteger, Column, String

from app.db import Base


class Region(Base):
    __tablename__ = "region"
    region_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
