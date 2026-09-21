from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.token import TokenBalance, TokenTransaction


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, student_id: int) -> TokenBalance | None:
        return self.db.query(TokenBalance).filter(TokenBalance.student_id == student_id).first()

    def get_or_create_balance(self, student_id: int) -> TokenBalance:
        balance = self.get_balance(student_id)
        if not balance:
            balance = TokenBalance(student_id=student_id, balance=0)
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
        return balance

    def update_balance(self, balance: TokenBalance) -> TokenBalance:
        self.db.commit()
        self.db.refresh(balance)
        return balance

    def add_transaction(self, transaction: TokenTransaction) -> TokenTransaction:
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_history(self, student_id: int) -> list[TokenTransaction]:
        return self.db.query(TokenTransaction).filter(
            TokenTransaction.student_id == student_id
        ).order_by(TokenTransaction.created_at.desc()).all()

    def get_award_transaction_for_report(self, report_id: int) -> TokenTransaction | None:
        return self.db.query(TokenTransaction).filter(
            TokenTransaction.related_report_id == report_id,
            TokenTransaction.transaction_type == "award"
        ).first()

    def get_by_redemption_reference(self, reference: str) -> TokenTransaction | None:
        """Look up a voucher by its UUID reference string (used by fulfillment staff)."""
        return self.db.query(TokenTransaction).filter(
            TokenTransaction.redemption_reference == reference
        ).first()

    def fulfill_transaction(self, transaction: TokenTransaction) -> TokenTransaction:
        """Mark a redemption voucher as fulfilled."""
        from datetime import datetime
        transaction.fulfillment_status = "Fulfilled"
        transaction.fulfilled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def total_awarded(self) -> int:
        result = self.db.query(func.sum(TokenTransaction.amount)).filter(
            TokenTransaction.transaction_type == "award"
        ).scalar()
        return result or 0

    def total_redeemed(self) -> int:
        result = self.db.query(func.sum(TokenTransaction.amount)).filter(
            TokenTransaction.transaction_type == "redeem"
        ).scalar()
        return result or 0

    def get_token_summary(self) -> list[dict]:
        awarded = self.total_awarded()
        redeemed = self.total_redeemed()
        return [
            {"label": "Awarded", "value": awarded},
            {"label": "Redeemed", "value": redeemed},
            {"label": "Outstanding", "value": awarded - redeemed},
        ]
