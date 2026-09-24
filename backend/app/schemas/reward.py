from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class RewardCatalogItemResponse(BaseModel):
    id: int
    name: str
    description: str
    token_cost: int
    # "Canteen" | "Laundry" | "Hostel Stores"
    category: str
    provider_location: Optional[str] = ""
    is_active: bool

    class Config:
        from_attributes = True


class RewardAdminResponse(BaseModel):
    """Full reward details for admin management (includes inactive, timestamps)."""
    id: int
    name: str
    description: str
    token_cost: int
    category: str
    provider_location: Optional[str] = ""
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RewardCreateRequest(BaseModel):
    """Payload for creating a new reward catalog item."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    token_cost: int = Field(..., gt=0)
    category: str = Field(..., description="Canteen | Laundry | Hostel Stores")
    provider_location: Optional[str] = Field(default="", max_length=100)


class RewardUpdateRequest(BaseModel):
    """Payload for updating an existing reward catalog item (all fields optional)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    token_cost: Optional[int] = Field(default=None, gt=0)
    category: Optional[str] = None
    provider_location: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class RewardRedeemResponse(BaseModel):
    message: str
    reward_name: str
    reward_category: str
    tokens_deducted: int
    remaining_balance: int
    transaction_id: int
    voucher_reference: str    # UUID-based code shown to staff for fulfillment
    created_at: datetime
