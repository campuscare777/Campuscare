from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.report import Report, ReportStatusHistory
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenAwardService
from app.models.user import COMPLAINT_STAFF_ROLES

# HostelCare valid status lifecycle
VALID_STATUSES = [
    "Submitted",
    "Under Review",
    "Verified by Food Staff",
    "Verified by Warden",
    "Verified",
    "Admin Verified",
    "In Progress",
    "Work Completed",
    "Resolved",
    "Rejected",
    "Duplicate",
]

# Backward-compat alias — use COMPLAINT_STAFF_ROLES directly in new code
STAFF_ROLES = COMPLAINT_STAFF_ROLES


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.user_repo = UserRepository(db)
        self.token_service = TokenAwardService(db)

    def create_report(
        self,
        reporter_id: int,
        hostel_type: str,
        location: str,
        category: str,
        building: str = None,
        floor: str = None,
        area: str = None,
        description: str = None,
        photo_path: str = None,
    ) -> Report:
        if not hostel_type or not hostel_type.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hostel type is required (Boys Hostel / Girls Hostel / NRI Hostel)."
            )
        if not location or not location.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location is required."
            )
        if not category or not category.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complaint category is required."
            )

        food_related = (category.strip() == "Food/Mess")

        report = Report(
            reporter_id=reporter_id,
            hostel_type=hostel_type.strip(),
            location=location.strip(),
            building=building,
            floor=floor,
            area=area,
            category=category.strip(),
            food_related=food_related,
            description=description,
            photo_path=photo_path,
            status="Submitted",
        )
        return self.report_repo.create(report)

    def get_report(self, report_id: int) -> Report:
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return report

    def list_reports(
        self,
        status_filter: str = None,
        reporter_id: int = None,
        hostel_type: str = None,
        category: str = None,
        food_related: bool = None,
    ) -> list[Report]:
        return self.report_repo.get_all(
            status=status_filter,
            reporter_id=reporter_id,
            hostel_type=hostel_type,
            category=category,
            food_related=food_related,
        )

    def verify_report(self, report_id: int, staff_id: int, reason: str = None) -> Report:
        from datetime import datetime
        report = self.get_report(report_id)
        if report.status in ["Verified", "Assigned", "In Progress", "Resolved"]:
            if not report.verified_at:
                report.verified_at = datetime.utcnow()
                report.verified_by_id = staff_id
                self.report_repo.update(report)
            return report

        old_status = report.status
        report.status = "Verified"
        report.verified_at = datetime.utcnow()
        report.verified_by_id = staff_id

        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Verified",
            changed_by_id=staff_id,
            reason=reason or "Complaint verified by staff",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        self.token_service.award_tokens(report.reporter_id, report_id)
        return report

    def reject_report(self, report_id: int, staff_id: int, reason: str) -> Report:
        """Reject a complaint with a mandatory reason."""
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A reason is required when rejecting a complaint."
            )
        report = self.get_report(report_id)
        old_status = report.status
        report.status = "Rejected"
        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Rejected",
            changed_by_id=staff_id,
            reason=reason.strip(),
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        return report

    def assign_report(self, report_id: int, staff_id: int, assigned_team: str) -> Report:
        """Assign a verified complaint to a team."""
        report = self.get_report(report_id)
        old_status = report.status
        report.assigned_team = assigned_team
        report.status = "Assigned"
        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Assigned",
            changed_by_id=staff_id,
            reason=f"Assigned to {assigned_team}",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        return report

    def forward_to_admin(self, report_id: int, staff_id: int, staff_role: Optional[str] = None, reason: str = None) -> Report:
        """Food staff or Warden verifies the complaint and forwards it to Admin."""
        if not staff_role:
            from app.models.user import User
            user = self.db.query(User).filter(User.id == staff_id).first()
            staff_role = user.role if user else None

        report = self.get_report(report_id)
        is_food = report.food_related or report.category in ["Food/Mess", "Food & Mess"]

        if staff_role == "food_staff":
            if not is_food:
                raise HTTPException(status_code=403, detail="Food staff can only verify food/mess complaints.")
            new_status = "Verified by Food Staff"
            action_desc = "Food staff verified complaint and forwarded to Admin"
        elif staff_role in ["warden", "maintenance"]:
            if is_food:
                raise HTTPException(status_code=403, detail="Warden cannot verify food complaints (handled by Food Staff).")
            new_status = "Verified by Warden"
            action_desc = "Warden verified complaint and forwarded to Admin"
        elif staff_role == "admin":
            new_status = "Verified by Food Staff" if is_food else "Verified by Warden"
            action_desc = "Verified and forwarded to Admin"
        else:
            raise HTTPException(status_code=403, detail="Unauthorized role for verification.")

        old_status = report.status
        report.status = new_status
        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status=new_status,
            changed_by_id=staff_id,
            reason=reason or action_desc,
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        return report

    def admin_verify(self, report_id: int, admin_id: int, reason: str = None) -> Report:
        """Admin approves the forwarded complaint. Green tokens (10) are awarded to student."""
        from datetime import datetime
        report = self.get_report(report_id)

        # Enforce requirement: student submits -> warden/foodstaff verifies & forwards -> admin verifies
        if report.status not in ["Verified by Food Staff", "Verified by Warden"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admin can only verify complaints that have been verified and forwarded by Warden or Food Staff. Current status is '{report.status}'."
            )

        old_status = report.status
        report.status = "Admin Verified"
        report.verified_at = datetime.utcnow()
        report.verified_by_id = admin_id

        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Admin Verified",
            changed_by_id=admin_id,
            reason=reason or "Admin verified complaint. 10 Green Tokens generated for student.",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)

        # Award Green Tokens to student
        self.token_service.award_tokens(report.reporter_id, report_id)
        return report

    def complete_work(self, report_id: int, staff_id: int, staff_role: Optional[str] = None, reason: str = None) -> Report:
        """Staff (Warden or Food Staff) solves the issue on-site and reports back to Admin."""
        if not staff_role:
            from app.models.user import User
            user = self.db.query(User).filter(User.id == staff_id).first()
            staff_role = user.role if user else None

        if staff_role not in ["food_staff", "warden", "maintenance"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Warden or Food Staff can confirm work completion on-site."
            )

        report = self.get_report(report_id)

        # Enforce requirement: work completion can only follow admin verification
        if report.status != "Admin Verified":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work completion can only be reported for Admin Verified complaints. Current status is '{report.status}'."
            )

        is_food = report.food_related or report.category in ["Food/Mess", "Food & Mess"]

        if staff_role == "food_staff" and not is_food:
            raise HTTPException(status_code=403, detail="Food staff can only solve food/mess complaints.")
        if staff_role == "warden" and is_food:
            raise HTTPException(status_code=403, detail="Warden cannot solve food complaints.")

        old_status = report.status
        report.status = "Work Completed"
        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Work Completed",
            changed_by_id=staff_id,
            reason=reason or "Work solved on-site. Reported to Admin for final closure.",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        return report

    def admin_resolve(self, report_id: int, admin_id: int, reason: str = None) -> Report:
        """Admin reviews completed work and marks the complaint as final Resolved / Closed."""
        from datetime import datetime
        report = self.get_report(report_id)

        # Enforce requirement: until warden/foodstaff informs work completed to admin, admin cannot close the complaint
        if report.status != "Work Completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot close complaint until Warden or Food Staff informs work is completed. Current status is '{report.status}'."
            )

        old_status = report.status
        report.status = "Resolved"
        report.resolved_at = datetime.utcnow()

        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status="Resolved",
            changed_by_id=admin_id,
            reason=reason or "Admin confirmed resolution and closed the complaint.",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)
        return report

    def update_status(self, report_id: int, new_status: str, changed_by_id: int,
                      reason: str = None) -> Report:
        from datetime import datetime
        if new_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        report = self.get_report(report_id)
        old_status = report.status

        if new_status in ["Admin Verified", "Verified"]:
            report.verified_at = datetime.utcnow()
            report.verified_by_id = changed_by_id

        if new_status == "Resolved":
            if report.status != "Work Completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot close complaint until Warden or Food Staff informs work is completed. Current status is '{report.status}'."
                )
            report.resolved_at = datetime.utcnow()

        history = ReportStatusHistory(
            report_id=report_id,
            from_status=old_status,
            to_status=new_status,
            changed_by_id=changed_by_id,
            reason=reason,
        )
        self.report_repo.add_status_history(history)
        report.status = new_status
        self.report_repo.update(report)

        if new_status in ["Admin Verified", "Verified"]:
            self.token_service.award_tokens(report.reporter_id, report_id)

        return report

    def get_status_history(self, report_id: int) -> list[ReportStatusHistory]:
        return self.report_repo.get_status_history(report_id)
