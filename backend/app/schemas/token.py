from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TokenBalanceResponse(BaseModel):
    student_id: int
    balance: int
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenTransactionResponse(BaseModel):
    id: int
    student_id: int
    transaction_type: str
    amount: int
    related_report_id: Optional[int] = None
    related_reward_id: Optional[int] = None
    redemption_reference: Optional[str] = None
    fulfillment_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenHistoryResponse(BaseModel):
    transactions: List[TokenTransactionResponse]
    total: int


class FulfillmentLookupResponse(BaseModel):
    """Response when staff looks up a voucher reference."""
    transaction_id: int
    voucher_reference: str
    reward_name: str
    reward_category: str
    resident_name: Optional[str] = None
    tokens_deducted: int
    fulfillment_status: str
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
