from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory
from app.models.user import User
from app.repositories.lost_and_found_repository import LostAndFoundRepository
from app.schemas.lost_and_found import LostAndFoundCreate, LostAndFoundStatusUpdate, LostAndFoundUpdate


ALLOWED_STATUSES = {
    "Submitted",
    "Under Review",
    "Received by Staff",
    "Published",
    "Claim Requested",
    "Verified",
    "Returned",
    "Closed",
    "Rejected",
}

STAFF_ROLES = ["admin", "warden", "staff", "hostel_staff"]


class LostAndFoundService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LostAndFoundRepository(db)

    def create_report(self, reporter_id: int, payload: LostAndFoundCreate) -> LostAndFoundItemReport:
        """AC1: Create a new lost/found report with unique reference ID."""
        report = LostAndFoundItemReport(
            reporter_id=reporter_id,
            report_type=payload.report_type,
            item_category=payload.item_category,
            item_name=payload.item_name,
            description=payload.description,
            image_reference=payload.image_reference,
            hostel_type=payload.hostel_type,
            location=payload.location,
            date_lost_or_found=payload.date_lost_or_found,
            identifying_details=payload.identifying_details,
            status="Submitted",
        )
        return self.repo.create(report)

    def get_report(self, item_report_id: int) -> LostAndFoundItemReport:
        """AC1: Retrieve report by reference ID (item_report_id)."""
        report = self.repo.get_by_id(item_report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Lost & Found item report not found")
        
        # Attach reporter_name if available
        user = self.db.query(User).filter(User.id == report.reporter_id).first()
        if user:
            setattr(report, "reporter_name", user.full_name or user.username)
        return report

    def list_reports(
        self,
        report_type: Optional[str] = None,
        item_category: Optional[str] = None,
        status: Optional[str] = None,
        reporter_id: Optional[int] = None,
        hostel_type: Optional[str] = None,
        hide_closed: bool = False,
        search: Optional[str] = None,
    ) -> List[LostAndFoundItemReport]:
        """
        List reports with filtering.
        
        AC5: hide_closed=True excludes Closed and Returned items from the list.
        """
        reports = self.repo.get_all(
            report_type=report_type,
            item_category=item_category,
            status=status,
            reporter_id=reporter_id,
            hostel_type=hostel_type,
            search=search,
        )
        
        # AC4/AC5: Filter out closed items if requested
        if hide_closed:
            reports = [r for r in reports if r.status not in ["Closed", "Returned"]]
        
        # Attach reporter names
        for r in reports:
            user = self.db.query(User).filter(User.id == r.reporter_id).first()
            if user:
                setattr(r, "reporter_name", user.full_name or user.username)
        
        return reports

    def claim_report(
        self,
        item_report_id: int,
        claimant_id: int,
        claim_notes: Optional[str] = None,
        proof_details: Optional[str] = None,
    ) -> LostAndFoundItemReport:
        """
        AC5: Resident submits claim request on lost/found item.
        Transitions status to 'Claim Requested' for staff verification.
        """
        report = self.get_report(item_report_id)
        if report.status in ["Returned", "Closed"]:
            raise HTTPException(status_code=400, detail="Cannot claim an item that is already returned or closed")

        old_status = report.status
        report.status = "Claim Requested"

        user = self.db.query(User).filter(User.id == claimant_id).first()
        claimant_name = user.full_name or user.username if user else f"User #{claimant_id}"
        notes = []
        if proof_details:
            notes.append(f"Proof: {proof_details}")
        if claim_notes:
            notes.append(f"Notes: {claim_notes}")
        reason_str = f"Claim submitted by {claimant_name} ({user.role if user else 'resident'})"
        if notes:
            reason_str += " - " + "; ".join(notes)

        history = LostAndFoundStatusHistory(
            item_report_id=item_report_id,
            from_status=old_status,
            to_status="Claim Requested",
            changed_by_id=claimant_id,
            reason=reason_str,
            changed_at=datetime.utcnow(),
        )
        self.repo.add_status_history(history)
        return self.repo.update(report)

    def update_status(
        self,
        item_report_id: int,
        changed_by_id: int,
        payload: LostAndFoundStatusUpdate,
    ) -> LostAndFoundItemReport:
        """
        AC2: Update status with staff authorization.
        AC3: Save closure timestamp when item is returned/closed.
        """
        report = self.get_report(item_report_id)

        new_status = payload.status
        if new_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{new_status}'. Allowed statuses: {sorted(list(ALLOWED_STATUSES))}",
            )

        old_status = report.status
        report.status = new_status

        if payload.assigned_staff is not None:
            report.assigned_staff = payload.assigned_staff

        # AC3: Given an item is returned, when the report is closed, then the return/closure timestamp is saved.
        if new_status in ["Returned", "Closed"]:
            if payload.closed_at:
                report.closed_at = payload.closed_at
            elif not report.closed_at:
                report.closed_at = datetime.utcnow()
        elif payload.closed_at:
            report.closed_at = payload.closed_at

        # Save audit trail
        history = LostAndFoundStatusHistory(
            item_report_id=item_report_id,
            from_status=old_status,
            to_status=new_status,
            changed_by_id=changed_by_id,
            reason=payload.reason,
            changed_at=datetime.utcnow(),
        )
        self.repo.add_status_history(history)

        updated_report = self.repo.update(report)
        return updated_report

    def update_report(
        self,
        item_report_id: int,
        payload: LostAndFoundUpdate,
    ) -> LostAndFoundItemReport:
        """AC1: Update report details (reporter can edit their own)."""
        report = self.get_report(item_report_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "status" and value is not None:
                if value not in ALLOWED_STATUSES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status '{value}'. Allowed statuses: {sorted(list(ALLOWED_STATUSES))}",
                    )
                if value in ["Returned", "Closed"] and not report.closed_at and not payload.closed_at:
                    report.closed_at = datetime.utcnow()
            setattr(report, field, value)

        return self.repo.update(report)

    def get_status_history(self, item_report_id: int) -> List[LostAndFoundStatusHistory]:
        """Get audit trail of status changes."""
        self.get_report(item_report_id)
        return self.repo.get_status_history(item_report_id)