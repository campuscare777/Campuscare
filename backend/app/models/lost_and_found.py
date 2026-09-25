from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, ForeignKey
from app.db.session import Base


class LostAndFoundItemReport(Base):
    """HostelCare - Lost and Found database model (HOSTELCARE-F004-DB-001)."""
    __tablename__ = "lost_and_found_reports"

    item_report_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    report_type: Mapped[str] = mapped_column(String(30))                     # "Lost" or "Found"
    item_category: Mapped[str] = mapped_column(String(50))                   # Electronics, Clothing, Keys, Books, etc.
    item_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # photo path/URL

    hostel_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Boys Hostel / Girls Hostel / NRI Hostel
    location: Mapped[str] = mapped_column(String(200))                       # location lost/found

    date_lost_or_found: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    identifying_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status: Submitted, Under Review, Published, Claim Requested, Verified, Returned, Closed, Rejected
    status: Mapped[str] = mapped_column(String(50), default="Submitted")
    assigned_staff: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @property
    def id(self) -> int:
        return self.item_report_id


class LostAndFoundStatusHistory(Base):
    """Audit trail of status updates for lost and found reports."""
    __tablename__ = "lost_and_found_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_report_id: Mapped[int] = mapped_column(ForeignKey("lost_and_found_reports.item_report_id"))
    from_status: Mapped[str] = mapped_column(String(50))
    to_status: Mapped[str] = mapped_column(String(50))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LostAndFoundClaim(Base):
    """HostelCare - Lost and Found Item Claim model (HOSTELCARE-F004-UI-004)."""
    __tablename__ = "lost_and_found_claims"

    claim_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_report_id: Mapped[int] = mapped_column(ForeignKey("lost_and_found_reports.item_report_id"))
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    identifying_info: Mapped[str] = mapped_column(Text)
    contact_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    claim_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status: Submitted, Verified, Rejected, Returned
    status: Mapped[str] = mapped_column(String(50), default="Submitted")
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verified_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_by_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    handed_over_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def id(self) -> int:
        return self.claim_id

