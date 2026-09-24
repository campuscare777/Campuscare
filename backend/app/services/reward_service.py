from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.reward_repository import RewardCatalogRepository
from app.models.reward import RewardCatalogItem


class RewardCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.reward_repo = RewardCatalogRepository(db)

    def get_all_rewards(self) -> list[RewardCatalogItem]:
        return self.reward_repo.get_all_active()

    def get_all_rewards_admin(self) -> list[RewardCatalogItem]:
        """Return ALL rewards (active + inactive) for admin management view."""
        return self.reward_repo.get_all()

    def get_rewards_by_category(self, category: str) -> list[RewardCatalogItem]:
        """Return active rewards filtered by category: Canteen / Laundry / Hostel Stores."""
        return self.reward_repo.get_by_category(category)

    def get_reward(self, reward_id: int) -> RewardCatalogItem:
        reward = self.reward_repo.get_by_id(reward_id)
        if not reward:
            raise HTTPException(status_code=404, detail="Reward not found")
        return reward

    def create_reward(self, name: str, description: str, token_cost: int,
                      category: str, provider_location: str = "") -> RewardCatalogItem:
        """Create a new reward catalog item."""
        item = RewardCatalogItem(
            name=name,
            description=description,
            token_cost=token_cost,
            category=category,
            provider_location=provider_location,
            is_active=True,
        )
        return self.reward_repo.create(item)

    def update_reward(self, reward_id: int, **kwargs) -> RewardCatalogItem:
        """Update an existing reward's fields. Raises 404 if not found."""
        # Filter out None values unless explicitly toggling is_active
        update_data = {k: v for k, v in kwargs.items() if v is not None or k == "is_active"}
        item = self.reward_repo.update(reward_id, **update_data)
        if not item:
            raise HTTPException(status_code=404, detail="Reward not found")
        return item

    def delete_reward(self, reward_id: int) -> RewardCatalogItem:
        """Soft-delete a reward by setting is_active=False. Raises 404 if not found."""
        item = self.reward_repo.soft_delete(reward_id)
        if not item:
            raise HTTPException(status_code=404, detail="Reward not found")
        return item
