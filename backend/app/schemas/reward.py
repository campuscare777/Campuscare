from pydantic import BaseModel
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


class RewardRedeemResponse(BaseModel):
    message: str
    reward_name: str
    reward_category: str
    tokens_deducted: int
    remaining_balance: int
    transaction_id: int
    voucher_reference: str    # UUID-based code shown to staff for fulfillment
    created_at: datetime
