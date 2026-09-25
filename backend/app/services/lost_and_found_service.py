from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory, LostAndFoundClaim
from app.models.user import User, COMPLAINT_STAFF_ROLES
from app.repositories.lost_and_found_repository import LostAndFoundRepository
from app.schemas.lost_and_found import LostAndFoundCreate, LostAndFoundStatusUpdate, LostAndFoundUpdate
from app.services.notification_service import NotificationService


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

STAFF_ROLES = list(COMPLAINT_STAFF_ROLES)


class LostAndFoundService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LostAndFoundRepository(db)
        self.notif_service = NotificationService(db)

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
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
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
            date_from=date_from,
            date_to=date_to,
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
        identifying_info: Optional[str] = None,
        contact_number: Optional[str] = None,
    ) -> LostAndFoundItemReport:
        """
        AC1, AC2: Resident submits claim request on lost/found item.
        Creates a LostAndFoundClaim and transitions item status to 'Claim Requested' for staff verification.
        """
        report = self.get_report(item_report_id)
        if report.status in ["Returned", "Closed"]:
            raise HTTPException(status_code=400, detail="Cannot claim an item that is already returned or closed")

        # Resolve identifying information from identifying_info or proof_details
        effective_proof = (identifying_info or proof_details or claim_notes or "").strip()
        if not effective_proof:
            raise HTTPException(
                status_code=400,
                detail="Identifying information or proof details is required to submit a claim",
            )

        # Create persistent claim request (AC2)
        claim = LostAndFoundClaim(
            item_report_id=item_report_id,
            claimant_id=claimant_id,
            identifying_info=effective_proof,
            contact_number=contact_number.strip() if contact_number else None,
            claim_notes=claim_notes.strip() if claim_notes else None,
            status="Submitted",
        )
        self.repo.create_claim(claim)

        old_status = report.status
        report.status = "Claim Requested"

        user = self.db.query(User).filter(User.id == claimant_id).first()
        claimant_name = user.full_name or user.username if user else f"User #{claimant_id}"
        notes = []
        if effective_proof:
            notes.append(f"Proof: {effective_proof}")
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
        updated_report = self.repo.update(report)

        # Notify claimant of submitted claim
        self.notif_service.create_notification(
            user_id=claimant_id,
            title="Claim Submitted",
            message=f"Your claim for found item '{report.item_name}' has been submitted and is pending staff verification.",
            event_type="claim_submitted",
            reference_id=claim.claim_id,
            reference_type="claim",
        )

        return updated_report

    submit_claim = claim_report

    def get_claim(self, claim_id: int) -> LostAndFoundClaim:
        """Retrieve claim by ID."""
        claim = self.repo.get_claim(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim request not found")
        self._enrich_claim(claim)
        return claim

    def _enrich_claim(self, claim: LostAndFoundClaim) -> None:
        """Helper to attach claimant and item metadata to a claim object."""
        claimant = self.db.query(User).filter(User.id == claim.claimant_id).first()
        if claimant:
            setattr(claim, "claimant_name", claimant.full_name or claimant.username)
            setattr(claim, "claimant_role", claimant.role)
        item = self.repo.get_by_id(claim.item_report_id)
        if item:
            setattr(claim, "item_name", item.item_name)
            setattr(claim, "item_category", item.item_category)
            setattr(claim, "item_location", item.location)
            setattr(claim, "item_status", item.status)

    def list_claims(
        self,
        item_report_id: Optional[int] = None,
        claimant_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[LostAndFoundClaim]:
        """List claims with optional filters and attached metadata."""
        claims = self.repo.get_claims(
            item_report_id=item_report_id,
            claimant_id=claimant_id,
            status=status,
        )
        for c in claims:
            self._enrich_claim(c)
        return claims

    def review_claim(
        self,
        claim_id: int,
        staff_user: User,
        action: str,
        rejection_reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> LostAndFoundClaim:
        """
        AC3 & AC4: Staff approves or rejects a claim.
        - Approve (AC3): claim status -> 'Verified', item status -> 'Verified'
        - Reject (AC4): requires rejection reason, claim status -> 'Rejected', stores reason shown to claimant
        """
        if staff_user.role not in STAFF_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only authorized staff can review item claims",
            )

        claim = self.get_claim(claim_id)
        report = self.get_report(claim.item_report_id)
        staff_name = staff_user.full_name or staff_user.username

        if action.lower() == "approve":
            claim.status = "Verified"
            claim.verified_by_id = staff_user.id
            claim.verified_by_name = staff_name
            claim.verified_at = datetime.utcnow()
            claim.rejection_reason = None
            self.repo.update_claim(claim)

            # Update item report status to 'Verified' (AC3)
            old_status = report.status
            report.status = "Verified"
            report.assigned_staff = staff_name
            self.repo.update(report)

            # Audit history
            history = LostAndFoundStatusHistory(
                item_report_id=report.item_report_id,
                from_status=old_status,
                to_status="Verified",
                changed_by_id=staff_user.id,
                reason=f"Claim #{claim.claim_id} approved and verified by staff {staff_name}. {notes or ''}".strip(),
                changed_at=datetime.utcnow(),
            )
            self.repo.add_status_history(history)

            # AC3: Notify claimant of claim approval / verification
            self.notif_service.notify_claim_status_updated(
                user_id=claim.claimant_id,
                claim_id=claim.claim_id,
                item_title=report.item_name,
                new_status="Verified",
            )

        elif action.lower() == "reject":
            if not rejection_reason or not rejection_reason.strip():
                raise HTTPException(
                    status_code=400,
                    detail="A rejection reason is required when rejecting a claim",
                )

            claim.status = "Rejected"
            claim.rejection_reason = rejection_reason.strip()
            claim.verified_by_id = staff_user.id
            claim.verified_by_name = staff_name
            claim.verified_at = datetime.utcnow()
            self.repo.update_claim(claim)

            # AC3: Notify claimant of claim rejection with reason
            self.notif_service.notify_claim_status_updated(
                user_id=claim.claimant_id,
                claim_id=claim.claim_id,
                item_title=report.item_name,
                new_status="Rejected",
                rejection_reason=rejection_reason.strip(),
            )

            # If there are no other active pending claims on this item, revert item status
            pending_claims = [
                c for c in self.repo.get_claims(item_report_id=report.item_report_id)
                if c.claim_id != claim.claim_id and c.status in ["Submitted", "Verified"]
            ]
            if not pending_claims:
                old_status = report.status
                report.status = "Published" if report.report_type == "Lost" else "Received by Staff"
                self.repo.update(report)
                history = LostAndFoundStatusHistory(
                    item_report_id=report.item_report_id,
                    from_status=old_status,
                    to_status=report.status,
                    changed_by_id=staff_user.id,
                    reason=f"Claim #{claim.claim_id} rejected by {staff_name}: {rejection_reason.strip()}",
                    changed_at=datetime.utcnow(),
                )
                self.repo.add_status_history(history)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid review action '{action}'. Must be 'approve' or 'reject'.",
            )

        self._enrich_claim(claim)
        return claim

    def confirm_handover(
        self,
        claim_id: int,
        staff_user: User,
        handover_notes: Optional[str] = None,
    ) -> LostAndFoundClaim:
        """
        AC5: Given an item is handed over, when staff confirm the handover,
        then the item report status changes to 'Returned'.
        """
        if staff_user.role not in STAFF_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only authorized staff can confirm item handover",
            )

        claim = self.get_claim(claim_id)
        if claim.status not in ["Verified", "Submitted"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot confirm handover for claim with status '{claim.status}'. Claim must be Verified.",
            )

        staff_name = staff_user.full_name or staff_user.username
        now_dt = datetime.utcnow()

        # Update claim
        claim.status = "Returned"
        claim.handed_over_at = now_dt
        self.repo.update_claim(claim)

        # Update item report (AC5)
        report = self.get_report(claim.item_report_id)
        old_status = report.status
        report.status = "Returned"
        report.closed_at = now_dt
        report.assigned_staff = staff_name
        self.repo.update(report)

        # Audit history
        history = LostAndFoundStatusHistory(
            item_report_id=report.item_report_id,
            from_status=old_status,
            to_status="Returned",
            changed_by_id=staff_user.id,
            reason=f"Item handover confirmed to claimant #{claim.claimant_id} by staff {staff_name}. {handover_notes or ''}".strip(),
            changed_at=now_dt,
        )
        self.repo.add_status_history(history)

        # Notify claimant of handover completion
        self.notif_service.notify_item_handover_confirmed(
            user_id=claim.claimant_id,
            item_id=report.item_report_id,
            item_title=report.item_name,
        )

        self._enrich_claim(claim)
        return claim


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