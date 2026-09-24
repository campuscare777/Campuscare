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

    def get_all(self) -> list[RewardCatalogItem]:
        """Return ALL rewards (active and inactive) for admin view."""
        return self.db.query(RewardCatalogItem).order_by(RewardCatalogItem.id.desc()).all()

    def get_by_category(self, category: str) -> list[RewardCatalogItem]:
        return self.db.query(RewardCatalogItem).filter(
            RewardCatalogItem.category == category, RewardCatalogItem.is_active == True
        ).all()

    def create(self, item: RewardCatalogItem) -> RewardCatalogItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, **kwargs) -> RewardCatalogItem | None:
        """Partially update a reward catalog item by id. Returns updated item or None."""
        item = self.get_by_id(item_id)
        if not item:
            return None
        for field, value in kwargs.items():
            if value is not None or field == "is_active":
                setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def soft_delete(self, item_id: int) -> RewardCatalogItem | None:
        """Soft-delete by setting is_active=False. Returns the item or None."""
        item = self.get_by_id(item_id)
        if not item:
            return None
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def total_redeemed_count(self) -> int:
        from app.models.token import TokenTransaction
        return self.db.query(TokenTransaction).filter(
            TokenTransaction.transaction_type == "redeem"
        ).count()
