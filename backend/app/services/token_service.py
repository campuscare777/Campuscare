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


class RewardRedemptionService:
    def __init__(self, db: Session):
        self.db = db
        self.token_repo = TokenRepository(db)

    def redeem_reward(self, student_id: int, reward_id: int):
        from app.repositories.reward_repository import RewardCatalogRepository
        reward_repo = RewardCatalogRepository(self.db)
        reward = reward_repo.get_by_id(reward_id)
        if not reward:
            raise HTTPException(status_code=404, detail="Reward not found")
        if not reward.is_active:
            raise HTTPException(status_code=400, detail="Reward is no longer available")

        balance = self.token_repo.get_or_create_balance(student_id)
        if balance.balance < reward.token_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. You have {balance.balance} tokens, but this reward costs {reward.token_cost}."
            )

        balance.balance -= reward.token_cost
        self.token_repo.update_balance(balance)

        transaction = TokenTransaction(
            student_id=student_id,
            transaction_type="redeem",
            amount=reward.token_cost,
            related_reward_id=reward_id,
        )
        transaction = self.token_repo.add_transaction(transaction)

        return {
            "message": "Reward redeemed successfully",
            "reward_name": reward.name,
            "tokens_deducted": reward.token_cost,
            "remaining_balance": balance.balance,
            "transaction_id": transaction.id,
            "created_at": transaction.created_at,
        }
