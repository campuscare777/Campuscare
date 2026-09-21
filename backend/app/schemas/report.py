from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import Optional, List


class ReportCreate(BaseModel):
    """Input for creating a hostel complaint."""
    hostel_type: str                      # "Boys Hostel" | "Girls Hostel" | "NRI Hostel"
    location: str                         # descriptive location (block + area)
    building: Optional[str] = None
    floor: Optional[str] = None
    area: Optional[str] = None
    category: str                         # Electrical / Plumbing / Food/Mess …
    description: Optional[str] = None
    photo_path: Optional[str] = None      # photo is optional in HostelCare


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    hostel_type: Optional[str] = None
    location: str
    building: Optional[str] = None
    floor: Optional[str] = None
    area: Optional[str] = None
    category: Optional[str] = None
    food_related: bool = False
    description: Optional[str] = None
    photo_path: Optional[str] = None
    status: str
    assigned_team: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    reporter_name: Optional[str] = None

    @computed_field
    @property
    def verified(self) -> bool:
        return self.verified_at is not None or self.status in [
            "Verified", "Assigned", "In Progress", "Resolved"
        ]

    @computed_field
    @property
    def eligible_for_token(self) -> bool:
        return self.verified

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    """Generic status change (used by staff for In Progress, Assigned, etc.)."""
    status: Optional[str] = None
    reason: Optional[str] = None


class VerifyRequest(BaseModel):
    reason: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str   # mandatory per business rules


class AssignRequest(BaseModel):
    assigned_team: str


class StatusHistoryResponse(BaseModel):
    id: int
    report_id: int
    from_status: str
    to_status: str
    changed_by_id: int
    changed_by_name: Optional[str] = None
    reason: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
