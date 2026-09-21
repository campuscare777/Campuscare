from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey
from app.db.session import Base


class TokenBalance(Base):
    """Green Token balance per hostel resident."""
    __tablename__ = "token_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)  # resident user id
    balance: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenTransaction(Base):
    """Ledger entry for every token award or redemption."""
    __tablename__ = "token_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # resident user id
    transaction_type: Mapped[str] = mapped_column(String(20))         # "award" | "redeem"
    amount: Mapped[int] = mapped_column(Integer)
    related_report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reports.id"), nullable=True)
    related_reward_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reward_catalog_items.id"), nullable=True)
    # Voucher reference generated on redemption (UUID-based, shown to staff for fulfillment)
    redemption_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    fulfillment_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # None | "Pending" | "Fulfilled"
    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
