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
    related_report_id: Optional[int]
    related_reward_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenHistoryResponse(BaseModel):
    transactions: List[TokenTransactionResponse]
    total: int
