from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ReportCreate(BaseModel):
    location: str
    building: Optional[str] = None
    floor: Optional[str] = None
    area: Optional[str] = None
    description: Optional[str] = None
    photo_path: str


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    photo_path: str
    location: str
    building: Optional[str]
    floor: Optional[str]
    area: Optional[str]
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    reporter_name: Optional[str] = None

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class StatusHistoryResponse(BaseModel):
    id: int
    report_id: int
    from_status: str
    to_status: str
    changed_by_id: int
    changed_by_name: Optional[str] = None
    reason: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
