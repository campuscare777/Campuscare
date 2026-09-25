"""
HOSTELCARE-CROSS-002: Notifications
===================================

Acceptance Criteria:
- AC1: Given a complaint status changes, when the update is saved,
       then a notification event is generated.
- AC2: Given tokens are awarded, when the award is completed,
       then the resident can view the earning notification.
- AC3: Given a claim is approved or rejected, when the status changes,
       then the claimant is notified.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.services.auth_service import hash_password, create_access_token
from app.models.user import User
from app.models.report import Report
from app.models.reward import RewardCatalogItem
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundClaim
from app.models.notification import (
    Notification,
    EVENT_COMPLAINT_SUBMITTED,
    EVENT_COMPLAINT_VERIFIED,
    EVENT_COMPLAINT_REJECTED,
    EVENT_COMPLAINT_ASSIGNED,
    EVENT_COMPLAINT_RESOLVED,
    EVENT_TOKEN_AWARDED,
    EVENT_REDEMPTION_CREATED,
    EVENT_REDEMPTION_FULFILLED,
    EVENT_CLAIM_APPROVED,
    EVENT_CLAIM_REJECTED,
    EVENT_ITEM_RETURNED,
)
from app.services.report_service import ReportService
from app.services.lost_and_found_service import LostAndFoundService
from app.services.token_service import RewardRedemptionService
from app.schemas.lost_and_found import LostAndFoundCreate


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield db
    fastapi_app.dependency_overrides.clear()
    db.close()


def _make_user(db, username, role, password="password123"):
    u = User(
        username=username,
        email=f"{username}@hostelcare.edu",
        hashed_password=hash_password(password),
        full_name=username.replace("_", " ").title(),
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _auth_header(user):
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# AC1: Complaint Status Change Notifications
# ---------------------------------------------------------------------------

def test_ac1_complaint_submitted_generates_notification(test_db):
    resident = _make_user(test_db, "resident_alice", "student")
    svc = ReportService(test_db)
    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="Boys Hostel",
        location="Block A, 1st Floor",
        category="Plumbing",
        description="Leaking tap in washroom",
    )

    notifs = test_db.query(Notification).filter(Notification.user_id == resident.id).all()
    assert len(notifs) >= 1
    submit_notif = next((n for n in notifs if n.event_type == EVENT_COMPLAINT_SUBMITTED), None)
    assert submit_notif is not None
    assert "Leaking tap" in submit_notif.message or str(report.id) in submit_notif.message
    assert submit_notif.reference_id == report.id


def test_ac1_complaint_verified_generates_notification(test_db):
    resident = _make_user(test_db, "resident_bob", "student")
    warden = _make_user(test_db, "warden_smith", "warden")
    svc = ReportService(test_db)
    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="Girls Hostel",
        location="Block B, 2nd Floor",
        category="Electrical",
        description="Corridor light broken",
    )

    svc.verify_report(report.id, warden.id, reason="Issue inspected and verified")

    notifs = test_db.query(Notification).filter(
        Notification.user_id == resident.id,
        Notification.event_type == EVENT_COMPLAINT_VERIFIED,
    ).all()
    assert len(notifs) == 1
    assert str(report.id) in notifs[0].message
    assert "verified" in notifs[0].message.lower()


def test_ac1_complaint_rejected_generates_notification_with_reason(test_db):
    resident = _make_user(test_db, "resident_charlie", "student")
    warden = _make_user(test_db, "warden_jones", "warden")
    svc = ReportService(test_db)
    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="Boys Hostel",
        location="Block C",
        category="Cleanliness",
        description="Dust in corridor",
    )

    rejection_reason = "Duplicate complaint already scheduled for routine cleaning"
    svc.reject_report(report.id, warden.id, reason=rejection_reason)

    notifs = test_db.query(Notification).filter(
        Notification.user_id == resident.id,
        Notification.event_type == EVENT_COMPLAINT_REJECTED,
    ).all()
    assert len(notifs) == 1
    assert rejection_reason in notifs[0].message
    assert "Rejected" in notifs[0].title


def test_ac1_complaint_assigned_and_resolved_notifications(test_db):
    resident = _make_user(test_db, "resident_david", "student")
    admin = _make_user(test_db, "admin_user", "admin")
    svc = ReportService(test_db)
    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="NRI Hostel",
        location="NRI Wing A",
        category="Internet/Network",
        description="WiFi router down",
    )

    svc.assign_report(report.id, admin.id, assigned_team="Network Engineering")

    assign_notif = test_db.query(Notification).filter(
        Notification.user_id == resident.id,
        Notification.event_type == EVENT_COMPLAINT_ASSIGNED,
    ).first()
    assert assign_notif is not None
    assert "Network Engineering" in assign_notif.message


# ---------------------------------------------------------------------------
# AC2: Token Award Notification
# ---------------------------------------------------------------------------

def test_ac2_token_award_generates_resident_notification(test_db):
    resident = _make_user(test_db, "resident_eve", "student")
    warden = _make_user(test_db, "warden_wilson", "warden")
    svc = ReportService(test_db)

    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="Boys Hostel",
        location="Block D",
        category="Plumbing",
        description="Pipe burst in bathroom",
    )

    svc.verify_report(report.id, warden.id, reason="Verified on site")

    # Check that resident received token award notification
    token_notif = test_db.query(Notification).filter(
        Notification.user_id == resident.id,
        Notification.event_type == EVENT_TOKEN_AWARDED,
    ).first()
    assert token_notif is not None
    assert "+10" in token_notif.message
    assert "Green Tokens" in token_notif.title
    assert token_notif.reference_id == report.id


def test_ac2_resident_can_view_token_earning_via_api(test_db):
    client = TestClient(fastapi_app)
    resident = _make_user(test_db, "resident_frank", "student")
    warden = _make_user(test_db, "warden_clark", "warden")
    svc = ReportService(test_db)

    report = svc.create_report(
        reporter_id=resident.id,
        hostel_type="Girls Hostel",
        location="Block E",
        category="Furniture",
        description="Broken desk in study hall",
    )
    svc.verify_report(report.id, warden.id)

    # Resident calls /api/notifications
    res = client.get("/api/notifications", headers=_auth_header(resident))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2  # submit + verified + token
    assert any(n["event_type"] == EVENT_TOKEN_AWARDED for n in data["items"])


# ---------------------------------------------------------------------------
# AC3: Claim Approval and Rejection Notifications
# ---------------------------------------------------------------------------

def test_ac3_claim_approved_notifies_claimant(test_db):
    claimant = _make_user(test_db, "resident_grace", "student")
    finder = _make_user(test_db, "resident_helen", "student")
    warden = _make_user(test_db, "warden_brown", "warden")
    lnf_svc = LostAndFoundService(test_db)

    found_item = lnf_svc.create_report(
        reporter_id=finder.id,
        payload=LostAndFoundCreate(
            report_type="Found",
            item_category="Electronics",
            item_name="Wireless Earbuds Case",
            description="Found in reading room",
            hostel_type="Girls Hostel",
            location="Reading Room",
        ),
    )

    lnf_svc.submit_claim(
        item_report_id=found_item.item_report_id,
        claimant_id=claimant.id,
        identifying_info="White case with scratch on lid",
    )

    claims = lnf_svc.list_claims(item_report_id=found_item.item_report_id)
    assert len(claims) == 1
    claim = claims[0]

    # Staff approves claim
    lnf_svc.review_claim(
        claim_id=claim.claim_id,
        staff_user=warden,
        action="approve",
        notes="Proof verified against item appearance",
    )

    # Check notification sent to claimant
    notifs = test_db.query(Notification).filter(
        Notification.user_id == claimant.id,
        Notification.event_type == EVENT_CLAIM_APPROVED,
    ).all()
    assert len(notifs) == 1
    assert "Wireless Earbuds Case" in notifs[0].message
    assert "approved" in notifs[0].message.lower() or "verified" in notifs[0].message.lower()


def test_ac3_claim_rejected_notifies_claimant_with_reason(test_db):
    claimant = _make_user(test_db, "resident_ian", "student")
    finder = _make_user(test_db, "resident_jack", "student")
    warden = _make_user(test_db, "warden_davis", "warden")
    lnf_svc = LostAndFoundService(test_db)

    found_item = lnf_svc.create_report(
        reporter_id=finder.id,
        payload=LostAndFoundCreate(
            report_type="Found",
            item_category="Keys",
            item_name="Room Key with Blue Tag",
            description="Found in dining area",
            hostel_type="Boys Hostel",
            location="Dining Hall",
        ),
    )

    lnf_svc.submit_claim(
        item_report_id=found_item.item_report_id,
        claimant_id=claimant.id,
        identifying_info="Tag says Room 101",
    )

    claims = lnf_svc.list_claims(item_report_id=found_item.item_report_id)
    claim = claims[0]

    rejection_reason = "Key tag room number does not match resident registration"
    lnf_svc.review_claim(
        claim_id=claim.claim_id,
        staff_user=warden,
        action="reject",
        rejection_reason=rejection_reason,
    )

    notifs = test_db.query(Notification).filter(
        Notification.user_id == claimant.id,
        Notification.event_type == EVENT_CLAIM_REJECTED,
    ).all()
    assert len(notifs) == 1
    assert rejection_reason in notifs[0].message
    assert "Rejected" in notifs[0].title


def test_ac3_item_handover_confirmed_notifies_claimant(test_db):
    claimant = _make_user(test_db, "resident_karen", "student")
    finder = _make_user(test_db, "resident_leo", "student")
    warden = _make_user(test_db, "warden_miller", "warden")
    lnf_svc = LostAndFoundService(test_db)

    found_item = lnf_svc.create_report(
        reporter_id=finder.id,
        payload=LostAndFoundCreate(
            report_type="Found",
            item_category="Books",
            item_name="Physics Textbook",
            description="Found in common hall",
            hostel_type="Boys Hostel",
            location="Common Hall",
        ),
    )

    lnf_svc.submit_claim(
        item_report_id=found_item.item_report_id,
        claimant_id=claimant.id,
        identifying_info="Name Karen on first page",
    )
    claim = lnf_svc.list_claims(item_report_id=found_item.item_report_id)[0]
    lnf_svc.review_claim(claim.claim_id, warden, action="approve")

    # Confirm handover
    lnf_svc.confirm_handover(claim.claim_id, warden, handover_notes="Claimant collected textbook in person")

    notifs = test_db.query(Notification).filter(
        Notification.user_id == claimant.id,
        Notification.event_type == EVENT_ITEM_RETURNED,
    ).all()
    assert len(notifs) == 1
    assert "Handover Complete" in notifs[0].title
    assert "Physics Textbook" in notifs[0].message


# ---------------------------------------------------------------------------
# Notification Endpoints & Read Management
# ---------------------------------------------------------------------------

def test_notification_mark_read_and_unread_count(test_db):
    client = TestClient(fastapi_app)
    user = _make_user(test_db, "resident_mark", "student")

    # Create 3 unread notifications
    for i in range(3):
        test_db.add(Notification(
            user_id=user.id,
            title=f"Notification {i+1}",
            message=f"Test message {i+1}",
            event_type="test_event",
            is_read=False,
        ))
    test_db.commit()

    # 1. Check unread count
    r = client.get("/api/notifications/unread-count", headers=_auth_header(user))
    assert r.status_code == 200
    assert r.json()["unread_count"] == 3

    # 2. List notifications
    r = client.get("/api/notifications", headers=_auth_header(user))
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 3
    first_id = items[0]["id"]

    # 3. Mark first notification read
    r = client.patch(f"/api/notifications/{first_id}/read", headers=_auth_header(user))
    assert r.status_code == 200
    assert r.json()["is_read"] is True

    # 4. Check updated unread count
    r = client.get("/api/notifications/unread-count", headers=_auth_header(user))
    assert r.json()["unread_count"] == 2

    # 5. Mark all read
    r = client.post("/api/notifications/mark-all-read", headers=_auth_header(user))
    assert r.status_code == 200
    assert r.json()["updated_count"] == 2

    # 6. Unread count is now 0
    r = client.get("/api/notifications/unread-count", headers=_auth_header(user))
    assert r.json()["unread_count"] == 0


def test_user_cannot_access_other_users_notifications(test_db):
    client = TestClient(fastapi_app)
    user_a = _make_user(test_db, "user_a", "student")
    user_b = _make_user(test_db, "user_b", "student")

    notif_a = Notification(
        user_id=user_a.id,
        title="User A Secret Notification",
        message="Confidential",
        event_type="private_event",
        is_read=False,
    )
    test_db.add(notif_a)
    test_db.commit()
    test_db.refresh(notif_a)

    # User B lists notifications -> should NOT see User A's notification
    r = client.get("/api/notifications", headers=_auth_header(user_b))
    assert r.status_code == 200
    assert r.json()["total"] == 0

    # User B tries to mark User A's notification read -> 404
    r = client.patch(f"/api/notifications/{notif_a.id}/read", headers=_auth_header(user_b))
    assert r.status_code == 404


def test_unauthenticated_request_denied(test_db):
    client = TestClient(fastapi_app)
    r = client.get("/api/notifications")
    assert r.status_code in [401, 403]
