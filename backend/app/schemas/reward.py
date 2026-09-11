from pydantic import BaseModel
from datetime import datetime
from typing import List


class RewardCatalogItemResponse(BaseModel):
    id: int
    name: str
    description: str
    token_cost: int
    category: str
    is_active: bool

    class Config:
        from_attributes = True


class RewardRedeemResponse(BaseModel):
    message: str
    reward_name: str
    tokens_deducted: int
    remaining_balance: int
    transaction_id: int
    created_at: datetime
