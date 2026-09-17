from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.report import Report, ReportStatusHistory
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenAwardService


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.user_repo = UserRepository(db)
        self.token_service = TokenAwardService(db)

    def create_report(self, reporter_id: int, photo_path: str, location: str,
                      building: str = None, floor: str = None, area: str = None,
                      description: str = None) -> Report:
        if not photo_path or not str(photo_path).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both a photo and a location are required to submit a report"
            )
        if not location or not str(location).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both a photo and a location are required to submit a report"
            )

        report = Report(
            reporter_id=reporter_id,
            photo_path=photo_path,
            location=location.strip(),
            building=building,
            floor=floor,
            area=area,
            description=description,
            status="Reported",
        )
        return self.report_repo.create(report)

    def get_report(self, report_id: int) -> Report:
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    def list_reports(self, status_filter: str = None, reporter_id: int = None) -> list[Report]:
        return self.report_repo.get_all(status=status_filter, reporter_id=reporter_id)

    def verify_report(self, report_id: int, staff_id: int, reason: str = None) -> Report:
        from datetime import datetime
        report = self.get_report(report_id)
        if report.status in ["Verified", "In Progress", "Resolved"]:
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
            reason=reason or "Report verified by maintenance staff",
        )
        self.report_repo.add_status_history(history)
        self.report_repo.update(report)

        self.token_service.award_tokens(report.reporter_id, report_id)
        return report

    def update_status(self, report_id: int, new_status: str, changed_by_id: int,
                      reason: str = None) -> Report:
        from datetime import datetime
        valid_statuses = ["Reported", "Submitted", "Verified", "In Progress", "Resolved", "Rejected"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        report = self.get_report(report_id)
        old_status = report.status

        # Business Rule 5: A report can only reach Resolved or In Progress after passing through Verified
        if new_status in ["In Progress", "Resolved"]:
            is_verified = (report.verified_at is not None) or (old_status in ["Verified", "In Progress", "Resolved"])
            if not is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A report cannot reach In Progress or Resolved without being Verified first."
                )

        if new_status == "Verified":
            report.verified_at = datetime.utcnow()
            report.verified_by_id = changed_by_id

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

        if new_status == "Verified":
            self.token_service.award_tokens(report.reporter_id, report_id)

        return report

    def get_status_history(self, report_id: int) -> list[ReportStatusHistory]:
        return self.report_repo.get_status_history(report_id)
