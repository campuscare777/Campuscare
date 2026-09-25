"""
HOSTELCARE-F004-UI-002: Found Item Report Form & Workflow Test Suite

User Story:
  As a hostel resident, I want to report an item I found, so that its owner can be
  identified and the item can be returned.

Acceptance Criteria:
  AC1: Given a resident opens the found-item form, when it loads,
       then item details and found location fields are displayed.
  AC2: Given valid item details are submitted, when the request succeeds,
       then a found-item report is created.
  AC3: Given an image is uploaded, when the report is saved,
       then the image reference is stored.
  AC4: Given a found item is handed over to authorized staff,
       when staff confirm receipt, then the report status is updated.

Definition of Done:
  - Found-item form implemented and tested.
  - API implemented and tested.
"""

import os
import io
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models.user import User
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory
from app.services.lost_and_found_service import LostAndFoundService, ALLOWED_STATUSES
from app.services.auth_service import create_access_token


# ── Test Database & Fixtures ──────────────────────────────────────────────────

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

    # Seed test users: student resident and staff member
    student = User(
        username="resident_student",
        email="resident@campus.edu",
        hashed_password="hashedpassword",
        full_name="Resident Jane",
        role="student",
    )
    staff = User(
        username="hostel_warden",
        email="warden@campus.edu",
        hashed_password="hashedpassword",
        full_name="Warden Robert",
        role="warden",
    )
    unauthorized_user = User(
        username="another_student",
        email="another@campus.edu",
        hashed_password="hashedpassword",
        full_name="Another Student",
        role="student",
    )
    db.add_all([student, staff, unauthorized_user])
    db.commit()
    db.refresh(student)
    db.refresh(staff)
    db.refresh(unauthorized_user)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield {
        "db": db,
        "student": student,
        "staff": staff,
        "unauthorized": unauthorized_user,
    }

    fastapi_app.dependency_overrides.clear()
    db.close()


@pytest.fixture
def client():
    return TestClient(fastapi_app)


# ── AC1: Form Fields & Location Structure ────────────────────────────────────

def test_ac1_form_component_fields_and_contract():
    """
    AC1: Given a resident opens the found-item form, when it loads,
         then item details and found location fields are displayed.

    Verify frontend component contracts and field constants:
    - Item details fields: item_category, item_name, identifying_details, description
    - Found location fields: location, date_lost_or_found, hostel_type
    """
    # Verify frontend file exists and contains all required form fields
    form_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "FoundItemReportForm.jsx")
    assert os.path.exists(form_path), f"FoundItemReportForm.jsx does not exist at {form_path}"

    with open(form_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Required item details fields (AC1)
    assert 'id="item-category"' in content, "AC1: item-category select field missing in form"
    assert 'id="item-name"' in content, "AC1: item-name input field missing in form"
    assert 'id="identifying-details"' in content, "AC1: identifying-details input field missing in form"
    assert 'id="item-description"' in content, "AC1: item-description textarea field missing in form"

    # Required found location fields (AC1)
    assert 'id="found-location"' in content, "AC1: found-location select field missing in form"
    assert 'id="date-found"' in content, "AC1: date-found input field missing in form"
    assert 'id="hostel-type"' in content, "AC1: hostel-type select field missing in form"

    # Verify form header and submit button
    assert 'Report a Found Item' in content, "AC1: Form title header missing"
    assert 'id="found-item-submit-btn"' in content, "AC1: Form submit button missing"


# ── AC2: Valid Item Details Submission Creates Found-Item Report ───────────────

def test_ac2_valid_item_submission_creates_found_report(client, test_db):
    """
    AC2: Given valid item details are submitted, when the request succeeds,
         then a found-item report is created.
    """
    student = test_db["student"]
    token = create_access_token(data={"sub": str(student.id)})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "report_type": "Found",
        "item_category": "Electronics",
        "item_name": "Apple AirPods Pro with White Case",
        "location": "Library / Study Room",
        "hostel_type": "Boys Hostel",
        "date_lost_or_found": "2026-09-25",
        "identifying_details": "Case has a small Pikachu sticker on back",
        "description": "Found on the second floor study table near window",
    }

    response = client.post("/api/lost-and-found", json=payload, headers=headers)
    assert response.status_code == 201, f"Report creation failed: {response.text}"

    data = response.json()
    assert data["item_report_id"] is not None and data["item_report_id"] > 0
    assert data["report_type"] == "Found"
    assert data["item_category"] == "Electronics"
    assert data["item_name"] == payload["item_name"]
    assert data["location"] == payload["location"]
    assert data["hostel_type"] == payload["hostel_type"]
    assert data["identifying_details"] == payload["identifying_details"]
    assert data["description"] == payload["description"]
    assert data["status"] == "Submitted"
    assert data["reporter_id"] == student.id

    # Verify retrievable via GET endpoint
    get_res = client.get(f"/api/lost-and-found/{data['item_report_id']}", headers=headers)
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["item_report_id"] == data["item_report_id"]
    assert fetched["item_name"] == payload["item_name"]


def test_ac2_missing_required_fields_rejected(client, test_db):
    """
    AC2 validation: Missing required fields (item_category, item_name, location)
    must be rejected with 422 Unprocessable Entity.
    """
    student = test_db["student"]
    token = create_access_token(data={"sub": str(student.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Missing item_category and location
    incomplete_payload = {
        "report_type": "Found",
        "item_name": "Lost Wallet",
    }
    response = client.post("/api/lost-and-found", json=incomplete_payload, headers=headers)
    assert response.status_code == 422


# ── AC3: Image Upload & Reference Storage ─────────────────────────────────────

def test_ac3_image_upload_reference_stored(client, test_db):
    """
    AC3: Given an image is uploaded, when the report is saved,
         then the image reference is stored.
    """
    student = test_db["student"]
    token = create_access_token(data={"sub": str(student.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Simulate multipart/form-data upload with fake image content
    file_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB"
    files = {
        "image": ("found_watch.jpg", io.BytesIO(file_bytes), "image/jpeg"),
    }
    form_data = {
        "report_type": "Found",
        "item_category": "Jewellery / Accessories",
        "item_name": "Silver Fossil Watch",
        "location": "Gymnasium",
        "hostel_type": "Boys Hostel",
        "date_lost_or_found": "2026-09-25",
        "identifying_details": "Metal mesh strap with slight scratch on bezel",
        "description": "Found near the dumbbell rack",
    }

    response = client.post(
        "/api/lost-and-found",
        data=form_data,
        files=files,
        headers=headers,
    )
    assert response.status_code == 201, f"Multipart upload failed: {response.text}"

    data = response.json()
    assert data["image_reference"] is not None
    assert "found_watch.jpg" in data["image_reference"]
    assert data["image_reference"].startswith("uploads/lost-and-found/")

    # Verify persisted in database
    db = test_db["db"]
    record = db.query(LostAndFoundItemReport).filter_by(item_report_id=data["item_report_id"]).first()
    assert record is not None
    assert record.image_reference == data["image_reference"]


# ── AC4: Staff Handover & Status Update ────────────────────────────────────────

def test_ac4_staff_confirms_receipt_status_updated(client, test_db):
    """
    AC4: Given a found item is handed over to authorized staff,
         when staff confirm receipt, then the report status is updated.
    """
    student = test_db["student"]
    staff = test_db["staff"]
    db = test_db["db"]

    student_token = create_access_token(data={"sub": str(student.id)})
    staff_token = create_access_token(data={"sub": str(staff.id)})

    # Resident creates found item report
    create_res = client.post(
        "/api/lost-and-found",
        json={
            "report_type": "Found",
            "item_category": "Keys",
            "item_name": "Hostel Room Key with Blue Tag",
            "location": "Common Area / Corridor",
            "date_lost_or_found": "2026-09-25",
            "identifying_details": "Room 304 marked on key tag",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert create_res.status_code == 201
    item_report_id = create_res.json()["item_report_id"]
    assert create_res.json()["status"] == "Submitted"

    # Authorized staff confirms receipt of the handed over item (AC4)
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    status_update_payload = {
        "status": "Received by Staff",
        "assigned_staff": "Warden Robert",
        "reason": "Found item handed over at security desk by student resident",
    }

    update_res = client.patch(
        f"/api/lost-and-found/{item_report_id}/status",
        json=status_update_payload,
        headers=staff_headers,
    )
    assert update_res.status_code == 200, f"Status update failed: {update_res.text}"

    updated_data = update_res.json()
    assert updated_data["status"] == "Received by Staff"
    assert updated_data["assigned_staff"] == "Warden Robert"

    # Verify status history audit trail recorded the handover
    history_res = client.get(
        f"/api/lost-and-found/{item_report_id}/history",
        headers=staff_headers,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    latest_event = history[-1]
    assert latest_event["from_status"] == "Submitted"
    assert latest_event["to_status"] == "Received by Staff"
    assert latest_event["changed_by_id"] == staff.id
    assert "handed over" in latest_event["reason"].lower()


def test_ac4_unauthorized_resident_cannot_update_status(client, test_db):
    """
    AC4 authorization rule: Unauthorized resident/student cannot update status.
    Only authorized staff/admin are permitted.
    """
    student = test_db["student"]
    unauthorized = test_db["unauthorized"]

    student_token = create_access_token(data={"sub": str(student.id)})
    unauth_token = create_access_token(data={"sub": str(unauthorized.id)})

    # Student creates report
    create_res = client.post(
        "/api/lost-and-found",
        json={
            "report_type": "Found",
            "item_category": "Books / Stationery",
            "item_name": "Calculus Textbook",
            "location": "Library / Study Room",
            "date_lost_or_found": "2026-09-25",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert create_res.status_code == 201
    item_report_id = create_res.json()["item_report_id"]

    # Unauthorized student attempts status update -> must receive 403 Forbidden
    unauth_res = client.patch(
        f"/api/lost-and-found/{item_report_id}/status",
        json={"status": "Received by Staff"},
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert unauth_res.status_code == 403
    assert "Only staff/admin" in unauth_res.json()["detail"]


# ── Full Lifecycle Verification ───────────────────────────────────────────────

def test_full_found_item_lifecycle(client, test_db):
    """
    Verify complete lifecycle from reporting found item to return/closure.
    """
    student = test_db["student"]
    staff = test_db["staff"]
    student_token = create_access_token(data={"sub": str(student.id)})
    staff_token = create_access_token(data={"sub": str(staff.id)})

    # 1. Resident reports found item (AC1, AC2)
    res = client.post(
        "/api/lost-and-found",
        json={
            "report_type": "Found",
            "item_category": "Electronics",
            "item_name": "Blue Wireless Mouse",
            "location": "Dining Hall / Mess",
            "date_lost_or_found": "2026-09-25",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 201
    item_id = res.json()["item_report_id"]

    # 2. Item handed to staff -> Received by Staff (AC4)
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    client.patch(
        f"/api/lost-and-found/{item_id}/status",
        json={"status": "Received by Staff", "assigned_staff": "Warden Robert"},
        headers=staff_headers,
    )

    # 3. Staff publishes notice -> Published
    client.patch(
        f"/api/lost-and-found/{item_id}/status",
        json={"status": "Published"},
        headers=staff_headers,
    )

    # 4. Item returned to verified owner -> Returned (timestamp saved)
    close_res = client.patch(
        f"/api/lost-and-found/{item_id}/status",
        json={"status": "Returned", "reason": "Claimant verified by serial number"},
        headers=staff_headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "Returned"
    assert close_res.json()["closed_at"] is not None


if __name__ == "__main__":
    pytest.main(["-v", __file__])
