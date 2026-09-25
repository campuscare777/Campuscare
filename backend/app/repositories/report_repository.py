from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.report import Report, ReportStatusHistory
from datetime import datetime, timedelta
from typing import Optional, List


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, report_id: int) -> Report | None:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_all(
        self,
        status: Optional[str] = None,
        reporter_id: Optional[int] = None,
        hostel_type: Optional[str] = None,
        category: Optional[str] = None,
        food_related: Optional[bool] = None,
        block: Optional[str] = None,
        floor: Optional[str] = None,
        assigned_team: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Report]:
        query = self.db.query(Report)
        if status:
            query = query.filter(Report.status == status)
        if reporter_id:
            query = query.filter(Report.reporter_id == reporter_id)
        if hostel_type:
            query = query.filter(Report.hostel_type == hostel_type)
        if category:
            query = query.filter(Report.category == category)
        if food_related is not None:
            query = query.filter(Report.food_related == food_related)
        if block:
            query = query.filter(Report.building == block)
        if floor:
            query = query.filter(Report.floor == floor)
        if assigned_team:
            query = query.filter(Report.assigned_team == assigned_team)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        return query.order_by(Report.created_at.desc()).all()

    def get_food_complaints(self) -> list[Report]:
        """Convenience helper for the food/mess staff dashboard."""
        return self.db.query(Report).filter(Report.food_related == True).order_by(Report.created_at.desc()).all()

    def count_by_status(self) -> dict[str, int]:
        results = self.db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
        return {status: count for status, count in results}

    def count_recent(self, days: int = 30) -> dict[str, int]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        submitted = self.db.query(Report).filter(Report.created_at >= cutoff).count()
        resolved = self.db.query(Report).filter(
            Report.status == "Resolved", Report.updated_at >= cutoff
        ).count()
        return {"submitted": submitted, "resolved": resolved}

    def get_trend_data(self, days: int = 7) -> list[dict]:
        result = []
        for i in range(days - 1, -1, -1):
            date = datetime.utcnow() - timedelta(days=i)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            submitted = self.db.query(Report).filter(
                Report.created_at >= start, Report.created_at < end
            ).count()
            resolved = self.db.query(Report).filter(
                Report.status == "Resolved", Report.updated_at >= start, Report.updated_at < end
            ).count()
            result.append({
                "label": start.strftime("%b %d"),
                "submitted": submitted,
                "resolved": resolved,
            })
        return result

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update(self, report: Report) -> Report:
        self.db.commit()
        self.db.refresh(report)
        return report

    def add_status_history(self, history: ReportStatusHistory) -> ReportStatusHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_status_history(self, report_id: int) -> list[ReportStatusHistory]:
        return self.db.query(ReportStatusHistory).filter(
            ReportStatusHistory.report_id == report_id
        ).order_by(ReportStatusHistory.changed_at.desc()).all()
