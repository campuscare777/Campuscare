from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer
from app.db.session import Base


class RewardCatalogItem(Base):
    """HostelCare reward catalog – Canteen, Laundry, or Hostel Stores items."""
    __tablename__ = "reward_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    token_cost: Mapped[int] = mapped_column(Integer)
    # category: "Canteen" | "Laundry" | "Hostel Stores"
    category: Mapped[str] = mapped_column(String(50))
    provider_location: Mapped[str] = mapped_column(String(100), default="")  # e.g. "Main Canteen", "Ground Floor Laundry"
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
