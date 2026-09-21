from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.token_service import TokenAwardService, RewardRedemptionService
from app.schemas.token import TokenBalanceResponse, TokenHistoryResponse, FulfillmentLookupResponse
from app.schemas.reward import RewardCatalogItemResponse, RewardRedeemResponse
from app.services.reward_service import RewardCatalogService
from app.models.user import User
from app.services.report_service import STAFF_ROLES

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
def list_rewards(
    category: Optional[str] = Query(None, description="Filter by: Canteen, Laundry, Hostel Stores"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return reward catalog, optionally filtered by category (Canteen / Laundry / Hostel Stores)."""
    service = RewardCatalogService(db)
    if category:
        rewards = service.get_rewards_by_category(category)
    else:
        rewards = service.get_all_rewards()
    return [RewardCatalogItemResponse.model_validate(r) for r in rewards]


@router.post("/rewards/{reward_id}/redeem", response_model=RewardRedeemResponse)
def redeem_reward(reward_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Redeem a reward from the catalog. Returns a voucher_reference for staff fulfillment."""
    service = RewardRedemptionService(db)
    result = service.redeem_reward(current_user.id, reward_id)
    return RewardRedeemResponse(**result)


@router.get("/redemptions/{voucher_reference}", response_model=FulfillmentLookupResponse)
def lookup_redemption(
    voucher_reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff: look up a voucher reference to see reward details before fulfillment."""
    if current_user.role not in STAFF_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only staff can look up redemption vouchers")
    service = RewardRedemptionService(db)
    result = service.lookup_redemption(voucher_reference)
    return FulfillmentLookupResponse(**result)


@router.patch("/redemptions/{voucher_reference}/fulfill")
def fulfill_redemption(
    voucher_reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff: mark a redemption voucher as fulfilled after providing the reward."""
    if current_user.role not in STAFF_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only staff can fulfill redemption vouchers")
    service = RewardRedemptionService(db)
    return service.fulfill_redemption(voucher_reference, current_user.id)
