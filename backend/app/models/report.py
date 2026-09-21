from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from app.db.session import Base


class Report(Base):
    """HostelCare – hostel complaint record."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # HostelCare location fields
    hostel_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)   # Boys Hostel / Girls Hostel / NRI Hostel
    location: Mapped[str] = mapped_column(String(200))                               # block / common area label
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # block name
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Complaint classification
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)      # Electrical / Plumbing / Food/Mess …
    food_related: Mapped[bool] = mapped_column(Boolean, default=False)               # True when category == Food/Mess

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)   # optional in HostelCare

    # Lifecycle
    status: Mapped[str] = mapped_column(String(30), default="Submitted")
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportStatusHistory(Base):
    """Audit trail of every status transition on a hostel complaint."""
    __tablename__ = "report_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
