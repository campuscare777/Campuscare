from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.token_service import TokenAwardService, RewardRedemptionService
from app.schemas.token import TokenBalanceResponse, TokenHistoryResponse
from app.schemas.reward import RewardCatalogItemResponse, RewardRedeemResponse
from app.services.reward_service import RewardCatalogService
from app.models.user import User

router = APIRouter(prefix="/api", tags=["tokens"])


@router.get("/tokens/balance", response_model=TokenBalanceResponse)
def get_balance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TokenAwardService(db)
    balance = service.token_repo.get_or_create_balance(current_user.id)
    return TokenBalanceResponse.model_validate(balance)


@router.get("/tokens/history", response_model=TokenHistoryResponse)
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TokenAwardService(db)
    transactions = service.get_history(current_user.id)
    return TokenHistoryResponse(
        transactions=[t for t in transactions],
        total=len(transactions),
    )


@router.get("/rewards", response_model=list[RewardCatalogItemResponse])
def list_rewards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = RewardCatalogService(db)
    rewards = service.get_all_rewards()
    return [RewardCatalogItemResponse.model_validate(r) for r in rewards]


@router.post("/rewards/{reward_id}/redeem", response_model=RewardRedeemResponse)
def redeem_reward(reward_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = RewardRedemptionService(db)
    result = service.redeem_reward(current_user.id, reward_id)
    return RewardRedeemResponse(**result)
