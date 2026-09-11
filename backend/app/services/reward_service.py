from sqlalchemy.orm import Session
from app.repositories.reward_repository import RewardCatalogRepository
from app.models.reward import RewardCatalogItem


class RewardCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.reward_repo = RewardCatalogRepository(db)

    def get_all_rewards(self) -> list[RewardCatalogItem]:
        return self.reward_repo.get_all_active()

    def get_reward(self, reward_id: int) -> RewardCatalogItem:
        reward = self.reward_repo.get_by_id(reward_id)
        if not reward:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Reward not found")
        return reward
