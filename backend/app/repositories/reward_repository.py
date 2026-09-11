from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.reward import RewardCatalogItem


class RewardCatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: int) -> RewardCatalogItem | None:
        return self.db.query(RewardCatalogItem).filter(RewardCatalogItem.id == item_id).first()

    def get_all_active(self) -> list[RewardCatalogItem]:
        return self.db.query(RewardCatalogItem).filter(RewardCatalogItem.is_active == True).all()

    def get_by_category(self, category: str) -> list[RewardCatalogItem]:
        return self.db.query(RewardCatalogItem).filter(
            RewardCatalogItem.category == category, RewardCatalogItem.is_active == True
        ).all()

    def create(self, item: RewardCatalogItem) -> RewardCatalogItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def total_redeemed_count(self) -> int:
        from app.models.token import TokenTransaction
        return self.db.query(TokenTransaction).filter(
            TokenTransaction.transaction_type == "redeem"
        ).count()
