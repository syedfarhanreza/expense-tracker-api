from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    transactions = relationship(
        "Transaction",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="check_transaction_amount_positive",
        ),
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="check_transaction_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(10), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    owner = relationship("User", back_populates="transactions")
