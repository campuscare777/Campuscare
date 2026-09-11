from sqlalchemy.orm import Session
from app.models.user import User
from app.models.report import Report
from app.models.token import TokenTransaction, TokenBalance
from app.models.reward import RewardCatalogItem
from sqlalchemy import func


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_kpis(self) -> dict:
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        total_reports = self.db.query(Report).count()
        open_reports = self.db.query(Report).filter(
            Report.status.in_(["Submitted", "Verified", "In Progress"])
        ).count()
        resolved_reports = self.db.query(Report).filter(Report.status == "Resolved").count()
        tokens_awarded = self.db.query(func.sum(TokenTransaction.amount)).filter(
            TokenTransaction.transaction_type == "award"
        ).scalar() or 0
        rewards_redeemed = self.db.query(TokenTransaction).filter(
            TokenTransaction.transaction_type == "redeem"
        ).count()
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_reports": total_reports,
            "open_reports": open_reports,
            "resolved_reports": resolved_reports,
            "tokens_awarded": tokens_awarded,
            "rewards_redeemed": rewards_redeemed,
        }

    def get_status_distribution(self) -> list[dict]:
        results = self.db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
        return [{"label": status, "value": count} for status, count in results]

    def get_recent_reports(self, limit: int = 5) -> list[dict]:
        reports = self.db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "location": r.location,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ]
