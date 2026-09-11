from pydantic import BaseModel
from typing import Optional, List


class KPICard(BaseModel):
    title: str
    value: int
    change: Optional[str] = None
    icon: Optional[str] = None


class ChartDataPoint(BaseModel):
    label: str
    value: int


class TrendData(BaseModel):
    labels: List[str]
    submitted: List[int]
    resolved: List[int]


class DashboardResponse(BaseModel):
    kpis: List[KPICard]
    trend: TrendData
    status_distribution: List[ChartDataPoint]
    token_summary: List[ChartDataPoint]
    recent_reports: List[dict]
