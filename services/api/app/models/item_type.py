from sqlalchemy import BigInteger, Column, Integer, String

from app.db import Base


class ItemType(Base):
    __tablename__ = "item_type"
    type_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    group_id = Column(BigInteger, nullable=True)
    category_id = Column(BigInteger, nullable=True)
    metagroup_id = Column(Integer, nullable=True)
    slot_hint = Column(String(16), nullable=True)
