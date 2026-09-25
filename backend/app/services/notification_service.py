from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import (
    Notification,
    EVENT_COMPLAINT_SUBMITTED,
    EVENT_COMPLAINT_VERIFIED,
    EVENT_COMPLAINT_REJECTED,
    EVENT_COMPLAINT_ASSIGNED,
    EVENT_COMPLAINT_IN_PROGRESS,
    EVENT_COMPLAINT_RESOLVED,
    EVENT_TOKEN_AWARDED,
    EVENT_REDEMPTION_CREATED,
    EVENT_REDEMPTION_FULFILLED,
    EVENT_CLAIM_STATUS_UPDATED,
    EVENT_CLAIM_SUBMITTED,
    EVENT_CLAIM_APPROVED,
    EVENT_CLAIM_REJECTED,
    EVENT_ITEM_RETURNED,
)
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        event_type: str,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            event_type=event_type,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )
        return self.repo.create(notif)

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        return self.repo.get_by_user(user_id, unread_only=unread_only, limit=limit, offset=offset)

    def get_unread_count(self, user_id: int) -> int:
        return self.repo.count_unread_by_user(user_id)

    def get_total_count(self, user_id: int, unread_only: bool = False) -> int:
        return self.repo.count_by_user(user_id, unread_only=unread_only)

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        return self.repo.mark_as_read(notification_id, user_id=user_id)

    def mark_all_as_read(self, user_id: int) -> int:
        return self.repo.mark_all_as_read(user_id)

    # -----------------------------------------------------------------------
    # Domain Notification Triggers
    # -----------------------------------------------------------------------

    def notify_complaint_submitted(self, user_id: int, report_id: int, description: str) -> Notification:
        desc_snippet = description[:60] + "..." if len(description) > 60 else description
        return self.create_notification(
            user_id=user_id,
            title="Complaint Submitted",
            message=f"Your complaint #{report_id} has been submitted successfully: \"{desc_snippet}\"",
            event_type=EVENT_COMPLAINT_SUBMITTED,
            reference_id=report_id,
            reference_type="complaint",
        )

    def notify_complaint_status_change(
        self,
        user_id: int,
        report_id: int,
        new_status: str,
        comment: Optional[str] = None,
    ) -> Notification:
        event_type_map = {
            "Verified": EVENT_COMPLAINT_VERIFIED,
            "Rejected": EVENT_COMPLAINT_REJECTED,
            "Assigned": EVENT_COMPLAINT_ASSIGNED,
            "In Progress": EVENT_COMPLAINT_IN_PROGRESS,
            "Resolved": EVENT_COMPLAINT_RESOLVED,
        }
        event_type = event_type_map.get(new_status, EVENT_COMPLAINT_VERIFIED)

        status_messages = {
            "Verified": f"Your complaint #{report_id} has been verified by staff.",
            "Rejected": f"Your complaint #{report_id} was rejected." + (f" Reason: {comment}" if comment else ""),
            "Assigned": f"Your complaint #{report_id} has been assigned for maintenance action." + (f" Note: {comment}" if comment else ""),
            "In Progress": f"Work on complaint #{report_id} is now in progress.",
            "Resolved": f"Complaint #{report_id} has been marked as resolved." + (f" Note: {comment}" if comment else ""),
        }
        msg = status_messages.get(new_status, f"Complaint #{report_id} status updated to {new_status}.")

        return self.create_notification(
            user_id=user_id,
            title=f"Complaint Status: {new_status}",
            message=msg,
            event_type=event_type,
            reference_id=report_id,
            reference_type="complaint",
        )

    def notify_token_awarded(
        self,
        user_id: int,
        amount: int,
        new_balance: int,
        report_id: Optional[int] = None,
    ) -> Notification:
        msg = f"You earned +{amount} Green Tokens for your verified complaint!"
        if report_id:
            msg += f" (Complaint #{report_id})"
        msg += f" Your new balance is {new_balance} tokens."
        return self.create_notification(
            user_id=user_id,
            title="Green Tokens Awarded!",
            message=msg,
            event_type=EVENT_TOKEN_AWARDED,
            reference_id=report_id,
            reference_type="token",
        )

    def notify_redemption_created(
        self,
        user_id: int,
        reward_name: str,
        voucher_code: str,
        token_cost: int,
        remaining_balance: int,
    ) -> Notification:
        return self.create_notification(
            user_id=user_id,
            title="Reward Redeemed",
            message=f"You redeemed '{reward_name}' for {token_cost} tokens. Voucher reference: {voucher_code}. Remaining balance: {remaining_balance}.",
            event_type=EVENT_REDEMPTION_CREATED,
            reference_id=None,
            reference_type="redemption",
        )

    def notify_redemption_fulfilled(
        self,
        user_id: int,
        reward_name: str,
        voucher_code: str,
    ) -> Notification:
        return self.create_notification(
            user_id=user_id,
            title="Redemption Fulfilled",
            message=f"Your voucher {voucher_code} for '{reward_name}' has been verified and fulfilled by counter staff.",
            event_type=EVENT_REDEMPTION_FULFILLED,
            reference_id=None,
            reference_type="redemption",
        )

    def notify_claim_status_updated(
        self,
        user_id: int,
        claim_id: int,
        item_title: str,
        new_status: str,
        rejection_reason: Optional[str] = None,
    ) -> Notification:
        if new_status == "Verified":
            title = "Item Claim Approved"
            msg = f"Your claim for found item '{item_title}' has been approved and verified! Please visit the warden/security desk with your ID to collect your item."
            event_type = EVENT_CLAIM_APPROVED
        elif new_status == "Rejected":
            title = "Item Claim Rejected"
            msg = f"Your claim for found item '{item_title}' was rejected."
            if rejection_reason:
                msg += f" Reason: {rejection_reason}"
            event_type = EVENT_CLAIM_REJECTED
        else:
            title = f"Claim Status: {new_status}"
            msg = f"Your claim for found item '{item_title}' is now {new_status}."
            event_type = EVENT_CLAIM_STATUS_UPDATED

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=msg,
            event_type=event_type,
            reference_id=claim_id,
            reference_type="claim",
        )

    def notify_item_handover_confirmed(
        self,
        user_id: int,
        item_id: int,
        item_title: str,
    ) -> Notification:
        return self.create_notification(
            user_id=user_id,
            title="Item Handover Complete",
            message=f"Handover confirmed for found item '{item_title}'. The item report status is now Returned.",
            event_type=EVENT_ITEM_RETURNED,
            reference_id=item_id,
            reference_type="lost_and_found",
        )
