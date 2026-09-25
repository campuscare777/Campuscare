import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.token_repository import TokenRepository
from app.models.token import TokenTransaction
from app.core.config import get_settings

settings = get_settings()


class TokenAwardService:
    def __init__(self, db: Session):
        self.db = db
        self.token_repo = TokenRepository(db)

    def award_tokens(self, student_id: int, report_id: int) -> TokenTransaction:
        existing_tx = self.token_repo.get_award_transaction_for_report(report_id)
        if existing_tx:
            return existing_tx

        balance = self.token_repo.get_or_create_balance(student_id)
        amount = settings.TOKEN_AWARD_AMOUNT
        balance.balance += amount
        self.token_repo.update_balance(balance)

        transaction = TokenTransaction(
            student_id=student_id,
            transaction_type="award",
            amount=amount,
            related_report_id=report_id,
        )
        return self.token_repo.add_transaction(transaction)

    def get_balance(self, student_id: int) -> int:
        balance = self.token_repo.get_or_create_balance(student_id)
        return balance.balance

    def get_history(self, student_id: int) -> list[TokenTransaction]:
        return self.token_repo.get_history(student_id)


FULFILLMENT_TEAMS = {
    "Canteen": "Canteen Team",
    "Laundry": "Laundry Team",
    "Hostel Stores": "Hostel Stores Team",
}


class RewardRedemptionService:
    def __init__(self, db: Session):
        self.db = db
        self.token_repo = TokenRepository(db)

    def redeem_reward(self, student_id: int, reward_id: int) -> dict:
        from app.repositories.reward_repository import RewardCatalogRepository
        reward_repo = RewardCatalogRepository(self.db)
        reward = reward_repo.get_by_id(reward_id)
        if not reward:
            raise HTTPException(status_code=404, detail="Reward not found")
        if not reward.is_active:
            raise HTTPException(status_code=400, detail="This reward is no longer available")

        balance = self.token_repo.get_or_create_balance(student_id)
        if balance.balance < reward.token_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. You have {balance.balance} tokens, but this reward costs {reward.token_cost}."
            )

        balance.balance -= reward.token_cost
        self.token_repo.update_balance(balance)

        # Generate a unique voucher reference for staff fulfillment
        voucher_ref = str(uuid.uuid4()).upper()[:12]  # e.g. "A1B2-C3D4-E5F6"

        transaction = TokenTransaction(
            student_id=student_id,
            transaction_type="redeem",
            amount=reward.token_cost,
            related_reward_id=reward_id,
            redemption_reference=voucher_ref,
            fulfillment_status="Pending",
        )
        transaction = self.token_repo.add_transaction(transaction)

        # Notify student of redemption
        from app.services.notification_service import NotificationService
        notif_service = NotificationService(self.db)
        notif_service.notify_redemption_created(
            user_id=student_id,
            reward_name=reward.name,
            voucher_code=voucher_ref,
            token_cost=reward.token_cost,
            remaining_balance=balance.balance,
        )

        return {
            "message": "Reward redeemed successfully",
            "reward_name": reward.name,
            "reward_category": reward.category,
            "tokens_deducted": reward.token_cost,
            "remaining_balance": balance.balance,
            "transaction_id": transaction.id,
            "voucher_reference": voucher_ref,
            "created_at": transaction.created_at,
        }

    def fulfill_redemption(self, voucher_reference: str, staff_id: int) -> dict:
        """Staff calls this to mark a voucher as fulfilled after handing over the reward."""
        from app.repositories.reward_repository import RewardCatalogRepository
        from app.services.notification_service import NotificationService
        voucher_reference = voucher_reference.strip().upper()
        tx = self.token_repo.get_by_redemption_reference(voucher_reference)
        if not tx:
            raise HTTPException(status_code=404, detail="Voucher reference not found")
        if tx.fulfillment_status == "Fulfilled":
            raise HTTPException(status_code=400, detail="This voucher has already been fulfilled")

        self.token_repo.fulfill_transaction(tx)

        reward_repo = RewardCatalogRepository(self.db)
        reward = reward_repo.get_by_id(tx.related_reward_id)
        reward_name = reward.name if reward else "Reward"

        notif_service = NotificationService(self.db)
        notif_service.notify_redemption_fulfilled(
            user_id=tx.student_id,
            reward_name=reward_name,
            voucher_code=voucher_reference,
        )

        return {
            "message": "Redemption fulfilled successfully",
            "voucher_reference": voucher_reference,
            "transaction_id": tx.id,
            "fulfilled_at": tx.fulfilled_at,
        }

    def lookup_redemption(self, voucher_reference: str) -> dict:
        """Staff calls this to look up a voucher before fulfilling it."""
        from app.repositories.reward_repository import RewardCatalogRepository
        voucher_reference = voucher_reference.strip().upper()
        tx = self.token_repo.get_by_redemption_reference(voucher_reference)
        if not tx:
            raise HTTPException(status_code=404, detail="Voucher reference not found")

        reward_repo = RewardCatalogRepository(self.db)
        reward = reward_repo.get_by_id(tx.related_reward_id)
        from app.models.user import User
        resident = self.db.query(User).filter(User.id == tx.student_id).first()

        return {
            "transaction_id": tx.id,
            "voucher_reference": voucher_reference,
            "reward_name": reward.name if reward else "Unknown",
            "reward_category": reward.category if reward else "Unknown",
            "tokens_deducted": tx.amount,
            "resident_name": resident.full_name if resident else None,
            "fulfillment_status": tx.fulfillment_status or "Pending",
            "fulfillment_team": FULFILLMENT_TEAMS.get(reward.category) if reward else None,
            "created_at": tx.created_at,
            "fulfilled_at": tx.fulfilled_at,
        }
