from pydantic import BaseModel, computed_field
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
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    reporter_name: Optional[str] = None

    @computed_field
    @property
    def verified(self) -> bool:
        return self.verified_at is not None or self.status in ["Verified", "In Progress", "Resolved"]

    @computed_field
    @property
    def eligible_for_token(self) -> bool:
        return self.verified

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
