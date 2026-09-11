from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey
from app.db.session import Base


class TokenBalance(Base):
    __tablename__ = "token_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    transaction_type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(Integer)
    related_report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id"), nullable=True)
    related_reward_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reward_catalog_items.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
