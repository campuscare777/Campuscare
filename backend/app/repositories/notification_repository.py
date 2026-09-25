from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_id(self, notification_id: int, user_id: Optional[int] = None) -> Optional[Notification]:
        q = self.db.query(Notification).filter(Notification.id == notification_id)
        if user_id is not None:
            q = q.filter(Notification.user_id == user_id)
        return q.first()

    def get_by_user(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        q = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            q = q.filter(Notification.is_read == False)
        return q.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()

    def count_unread_by_user(self, user_id: int) -> int:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

    def count_by_user(self, user_id: int, unread_only: bool = False) -> int:
        q = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            q = q.filter(Notification.is_read == False)
        return q.count()

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        notif = self.get_by_id(notification_id, user_id=user_id)
        if notif:
            notif.is_read = True
            self.db.commit()
            self.db.refresh(notif)
        return notif

    def mark_all_as_read(self, user_id: int) -> int:
        updated = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True}, synchronize_session=False)
        self.db.commit()
        return updated
