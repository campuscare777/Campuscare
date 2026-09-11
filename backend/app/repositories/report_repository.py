from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.report import Report, ReportStatusHistory
from datetime import datetime, timedelta


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, report_id: int) -> Report | None:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_all(self, status: str = None, reporter_id: int = None) -> list[Report]:
        query = self.db.query(Report)
        if status:
            query = query.filter(Report.status == status)
        if reporter_id:
            query = query.filter(Report.reporter_id == reporter_id)
        return query.order_by(Report.created_at.desc()).all()

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
