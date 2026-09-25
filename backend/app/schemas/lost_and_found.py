from pydantic import BaseModel, computed_field, ConfigDict
from datetime import datetime
from typing import Optional, List


class LostAndFoundCreate(BaseModel):
    """Input for creating a lost or found item report."""
    report_type: str                            # "Lost" | "Found"
    item_category: str                          # Electronics, Clothing, Keys, etc.
    item_name: str
    description: Optional[str] = None
    image_reference: Optional[str] = None
    hostel_type: Optional[str] = None           # "Boys Hostel" | "Girls Hostel" | "NRI Hostel"
    location: str
    date_lost_or_found: Optional[datetime] = None
    identifying_details: Optional[str] = None


class LostAndFoundStatusUpdate(BaseModel):
    """Input for staff status update on a lost/found report."""
    status: str
    assigned_staff: Optional[str] = None
    reason: Optional[str] = None
    closed_at: Optional[datetime] = None


class LostAndFoundClaimRequest(BaseModel):
    """Input for resident claiming a lost/found item report (AC1, AC2)."""
    identifying_info: Optional[str] = None
    proof_details: Optional[str] = None
    contact_number: Optional[str] = None
    claim_notes: Optional[str] = None


class LostAndFoundClaimReview(BaseModel):
    """Input for staff reviewing a claim (AC3, AC4)."""
    action: str  # "approve" | "reject"
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class LostAndFoundClaimHandover(BaseModel):
    """Input for staff confirming item handover (AC5)."""
    handover_notes: Optional[str] = None


class LostAndFoundClaimResponse(BaseModel):
    """Claim representation returned by API."""
    claim_id: int
    item_report_id: int
    claimant_id: int
    claimant_name: Optional[str] = None
    claimant_role: Optional[str] = None
    identifying_info: str
    contact_number: Optional[str] = None
    claim_notes: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    verified_by_id: Optional[int] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    handed_over_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    item_name: Optional[str] = None
    item_category: Optional[str] = None
    item_location: Optional[str] = None
    item_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def id(self) -> int:
        return self.claim_id




class LostAndFoundUpdate(BaseModel):
    """Input for editing lost and found details."""
    report_type: Optional[str] = None
    item_category: Optional[str] = None
    item_name: Optional[str] = None
    description: Optional[str] = None
    image_reference: Optional[str] = None
    hostel_type: Optional[str] = None
    location: Optional[str] = None
    date_lost_or_found: Optional[datetime] = None
    identifying_details: Optional[str] = None
    status: Optional[str] = None
    assigned_staff: Optional[str] = None
    closed_at: Optional[datetime] = None


class LostAndFoundResponse(BaseModel):
    item_report_id: int
    reporter_id: int
    report_type: str
    item_category: str
    item_name: str
    description: Optional[str] = None
    image_reference: Optional[str] = None
    hostel_type: Optional[str] = None
    location: str
    date_lost_or_found: Optional[datetime] = None
    identifying_details: Optional[str] = None
    status: str
    assigned_staff: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    reporter_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def id(self) -> int:
        return self.item_report_id


class LostAndFoundStatusHistoryResponse(BaseModel):
    id: int
    item_report_id: int
    from_status: str
    to_status: str
    changed_by_id: int
    reason: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LostAndFoundListResponse(BaseModel):
    reports: List[LostAndFoundResponse]
    total: int
