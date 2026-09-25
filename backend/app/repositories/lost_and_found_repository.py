from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory
from datetime import datetime
from typing import Optional, List


class LostAndFoundRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_report_id: int) -> Optional[LostAndFoundItemReport]:
        return self.db.query(LostAndFoundItemReport).filter(
            LostAndFoundItemReport.item_report_id == item_report_id
        ).first()

    def get_all(
        self,
        report_type: Optional[str] = None,
        item_category: Optional[str] = None,
        status: Optional[str] = None,
        reporter_id: Optional[int] = None,
        hostel_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[LostAndFoundItemReport]:
        query = self.db.query(LostAndFoundItemReport)
        if report_type and report_type != "All":
            query = query.filter(LostAndFoundItemReport.report_type == report_type)
        if item_category and item_category != "All":
            query = query.filter(LostAndFoundItemReport.item_category == item_category)
        if status and status != "All":
            query = query.filter(LostAndFoundItemReport.status == status)
        if reporter_id:
            query = query.filter(LostAndFoundItemReport.reporter_id == reporter_id)
        if hostel_type and hostel_type != "All":
            query = query.filter(LostAndFoundItemReport.hostel_type == hostel_type)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    LostAndFoundItemReport.item_name.ilike(term),
                    LostAndFoundItemReport.description.ilike(term),
                    LostAndFoundItemReport.location.ilike(term),
                    LostAndFoundItemReport.identifying_details.ilike(term),
                )
            )
        return query.order_by(LostAndFoundItemReport.created_at.desc()).all()

    def create(self, report: LostAndFoundItemReport) -> LostAndFoundItemReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update(self, report: LostAndFoundItemReport) -> LostAndFoundItemReport:
        report.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(report)
        return report

    def add_status_history(self, history: LostAndFoundStatusHistory) -> LostAndFoundStatusHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_status_history(self, item_report_id: int) -> List[LostAndFoundStatusHistory]:
        return self.db.query(LostAndFoundStatusHistory).filter(
            LostAndFoundStatusHistory.item_report_id == item_report_id
        ).order_by(LostAndFoundStatusHistory.changed_at.desc()).all()

    def count_by_status(self) -> dict:
        results = (
            self.db.query(LostAndFoundItemReport.status, func.count(LostAndFoundItemReport.item_report_id))
            .group_by(LostAndFoundItemReport.status)
            .all()
        )
        return {status: count for status, count in results}
