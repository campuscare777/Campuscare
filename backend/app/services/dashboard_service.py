from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.report_repository import ReportRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.dashboard_repo = DashboardRepository(db)
        self.token_repo = TokenRepository(db)
        self.report_repo = ReportRepository(db)

    def get_dashboard_data(self) -> dict:
        kpis_raw = self.dashboard_repo.get_kpis()
        kpis = [
            {"title": "Total Complaints", "value": kpis_raw["total_reports"], "icon": "FileText"},
            {"title": "Open Complaints", "value": kpis_raw["open_reports"], "icon": "AlertCircle"},
            {"title": "Resolved Complaints", "value": kpis_raw["resolved_reports"], "icon": "CheckCircle"},
            {"title": "Green Tokens Awarded", "value": kpis_raw["tokens_awarded"], "icon": "Coins"},
            {"title": "Rewards Redeemed", "value": kpis_raw["rewards_redeemed"], "icon": "Gift"},
            {"title": "Active Residents", "value": kpis_raw["active_users"], "icon": "Users"},
        ]

        trend = self.report_repo.get_trend_data(days=7)
        status_dist = self.dashboard_repo.get_status_distribution()
        token_summary = self.token_repo.get_token_summary()
        recent = self.dashboard_repo.get_recent_reports(limit=5)

        return {
            "kpis": kpis,
            "trend": {
                "labels": [t["label"] for t in trend],
                "submitted": [t["submitted"] for t in trend],
                "resolved": [t["resolved"] for t in trend],
            },
            "status_distribution": status_dist,
            "token_summary": token_summary,
            "recent_reports": recent,
        }
