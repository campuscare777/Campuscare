from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

EVENT_COMPLAINT_SUBMITTED = "complaint_submitted"
EVENT_COMPLAINT_VERIFIED = "complaint_verified"
EVENT_COMPLAINT_REJECTED = "complaint_rejected"
EVENT_COMPLAINT_ASSIGNED = "complaint_assigned"
EVENT_COMPLAINT_IN_PROGRESS = "complaint_in_progress"
EVENT_COMPLAINT_RESOLVED = "complaint_resolved"
EVENT_TOKEN_AWARDED = "token_awarded"
EVENT_REDEMPTION_CREATED = "redemption_created"
EVENT_REDEMPTION_FULFILLED = "redemption_fulfilled"
EVENT_CLAIM_STATUS_UPDATED = "claim_status_updated"
EVENT_CLAIM_SUBMITTED = "claim_submitted"
EVENT_CLAIM_APPROVED = "claim_approved"
EVENT_CLAIM_REJECTED = "claim_rejected"
EVENT_ITEM_RETURNED = "item_returned"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(64), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="notifications")
