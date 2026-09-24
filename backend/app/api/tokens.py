from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.token_service import TokenAwardService, RewardRedemptionService
from app.schemas.token import TokenBalanceResponse, TokenHistoryResponse, FulfillmentLookupResponse
from app.schemas.reward import (
    RewardCatalogItemResponse,
    RewardRedeemResponse,
    RewardAdminResponse,
    RewardCreateRequest,
    RewardUpdateRequest,
)
from app.services.reward_service import RewardCatalogService
from app.models.user import User
from app.services.report_service import STAFF_ROLES

router = APIRouter(prefix="/api", tags=["tokens"])

# Roles allowed to manage the reward catalog
REWARD_ADMIN_ROLES = {"admin", "warden"}


def _require_reward_admin(current_user: User) -> None:
    """Raise 403 if the current user is not an admin or warden."""
    if current_user.role not in REWARD_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: only admin or warden can manage rewards",
        )



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


# ---------------------------------------------------------------------------
# Admin / Warden: Reward Catalog Management (HOSTELCARE-F003-UI-004)
# ---------------------------------------------------------------------------

@router.get("/admin/rewards", response_model=list[RewardAdminResponse])
def admin_list_rewards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin/Warden: list ALL rewards including inactive ones (AC1)."""
    _require_reward_admin(current_user)
    service = RewardCatalogService(db)
    rewards = service.get_all_rewards_admin()
    return [RewardAdminResponse.model_validate(r) for r in rewards]


@router.post("/admin/rewards", response_model=RewardAdminResponse, status_code=201)
def admin_create_reward(
    payload: RewardCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin/Warden: create a new reward in the catalog (AC2)."""
    _require_reward_admin(current_user)
    service = RewardCatalogService(db)
    reward = service.create_reward(
        name=payload.name,
        description=payload.description,
        token_cost=payload.token_cost,
        category=payload.category,
        provider_location=payload.provider_location or "",
    )
    return RewardAdminResponse.model_validate(reward)


@router.put("/admin/rewards/{reward_id}", response_model=RewardAdminResponse)
def admin_update_reward(
    reward_id: int,
    payload: RewardUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin/Warden: update reward details, token cost, or availability (AC3)."""
    _require_reward_admin(current_user)
    service = RewardCatalogService(db)
    update_data = payload.model_dump(exclude_unset=True)
    reward = service.update_reward(reward_id, **update_data)
    return RewardAdminResponse.model_validate(reward)


@router.delete("/admin/rewards/{reward_id}", response_model=RewardAdminResponse)
def admin_delete_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin/Warden: soft-delete (deactivate) a reward from the catalog."""
    _require_reward_admin(current_user)
    service = RewardCatalogService(db)
    reward = service.delete_reward(reward_id)
    return RewardAdminResponse.model_validate(reward)
