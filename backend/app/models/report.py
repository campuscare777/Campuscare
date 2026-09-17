from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey
from app.db.session import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    photo_path: Mapped[str] = mapped_column(String(500))
    location: Mapped[str] = mapped_column(String(200))
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Reported")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    from_status: Mapped[str] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
