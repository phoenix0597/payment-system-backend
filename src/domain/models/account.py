from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from src.infrastructure.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Numeric(10, 2), default=0)

    user = relationship("User", back_populates="accounts")
    payments = relationship(
        "Payment", back_populates="account", cascade="all, delete-orphan"
    )
