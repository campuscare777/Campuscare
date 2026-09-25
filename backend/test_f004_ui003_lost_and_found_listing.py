"""
HOSTELCARE-F004-UI-003: Lost and Found Listing, Filtering & Claim Workflow Test Suite

User Story:
  As a hostel resident, I want to view relevant lost and found items, so that I can
  identify a missing belonging or help return a found item.

Acceptance Criteria:
  AC1: Given a resident opens the lost-and-found page, when it loads,
       then active item reports are displayed.
  AC2: Given a resident filters by category or hostel type, when the filter is applied,
       then matching reports are displayed.
  AC3: Given a resident opens an item report, when the details page loads,
       then the image, description, location, and report status are shown according to access permissions.
  AC4: Given an item has been returned or closed, when the listing loads,
       then it is marked as closed or removed from active listings.
  AC5: Given a resident wants to claim an item, when they submit a claim request,
       then the request is sent to authorized staff for verification.

Definition of Done:
  - Lost-and-found listing and filtering implemented and tested.
"""

import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.models.user import User
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory
from app.services.lost_and_found_service import LostAndFoundService
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

    # Seed users: 2 students and 1 warden staff
    student1 = User(
        username="resident_bob",
        email="bob@campus.edu",
        hashed_password="hashedpassword",
        full_name="Resident Bob",
        role="student",
    )
    student2 = User(
        username="resident_alice",
        email="alice@campus.edu",
        hashed_password="hashedpassword",
        full_name="Resident Alice",
        role="student",
    )
    warden = User(
        username="warden_mike",
        email="warden@campus.edu",
        hashed_password="hashedpassword",
        full_name="Warden Mike",
        role="warden",
    )
    db.add_all([student1, student2, warden])
    db.commit()
    db.refresh(student1)
    db.refresh(student2)
    db.refresh(warden)

    # Seed initial items across categories, hostel types, and statuses
    item_active_lost = LostAndFoundItemReport(
        reporter_id=student1.id,
        report_type="Lost",
        item_category="Electronics",
        item_name="Sony Wireless Headphones",
        description="Black noise-canceling headphones left in study hall.",
        image_reference="uploads/lost-and-found/sony_headphones.jpg",
        hostel_type="Boys Hostel",
        location="Reading Room Desk 12",
        date_lost_or_found=datetime.utcnow() - timedelta(days=2),
        identifying_details="Serial number SN-778844 on inner headband",
        status="Submitted",
    )
    item_active_found = LostAndFoundItemReport(
        reporter_id=student2.id,
        report_type="Found",
        item_category="Keys",
        item_name="Set of 3 Room Keys on Leather Ring",
        description="Found on the dining table after dinner.",
        image_reference="uploads/lost-and-found/found_keys.jpg",
        hostel_type="Girls Hostel",
        location="Dining Hall Table 4",
        date_lost_or_found=datetime.utcnow() - timedelta(days=1),
        identifying_details="Key tag labeled Room 302",
        status="Received by Staff",
        assigned_staff="Warden Mike",
    )
    item_clothing_found = LostAndFoundItemReport(
        reporter_id=student1.id,
        report_type="Found",
        item_category="Clothing",
        item_name="Blue Anna University Hoodie",
        description="Found in common room sofa.",
        image_reference=None,
        hostel_type="Boys Hostel",
        location="Hostel Block A Lounge",
        date_lost_or_found=datetime.utcnow() - timedelta(days=3),
        identifying_details="Size L with embroidered initial 'B'",
        status="Published",
    )
    item_closed = LostAndFoundItemReport(
        reporter_id=student2.id,
        report_type="Lost",
        item_category="Documents",
        item_name="Resident ID Card",
        description="Lost near campus gate.",
        image_reference="uploads/lost-and-found/id_card.jpg",
        hostel_type="NRI Hostel",
        location="Main Campus Entrance",
        date_lost_or_found=datetime.utcnow() - timedelta(days=7),
        identifying_details="ID: 2026-NRI-99",
        status="Returned",
        closed_at=datetime.utcnow() - timedelta(days=4),
    )

    db.add_all([item_active_lost, item_active_found, item_clothing_found, item_closed])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield {
        "db": db,
        "student1": student1,
        "student2": student2,
        "warden": warden,
        "item_active_lost": item_active_lost,
        "item_active_found": item_active_found,
        "item_clothing_found": item_clothing_found,
        "item_closed": item_closed,
    }

    fastapi_app.dependency_overrides.clear()
    db.close()


@pytest.fixture
def client():
    return TestClient(fastapi_app)


# ── AC1: Active item reports displayed when page loads ────────────────────────

def test_ac1_active_item_reports_displayed_on_load(client, test_db):
    """
    AC1: Given a resident opens the lost-and-found page, when it loads,
         then active item reports are displayed.
    """
    student1 = test_db["student1"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/lost-and-found", headers=headers)
    assert response.status_code == 200, f"Failed to list reports: {response.text}"

    data = response.json()
    assert "reports" in data
    assert data["total"] >= 3

    # Verify that active items from community are present
    names = [r["item_name"] for r in data["reports"]]
    assert "Sony Wireless Headphones" in names
    assert "Set of 3 Room Keys on Leather Ring" in names
    assert "Blue Anna University Hoodie" in names


# ── AC2: Filter by Category, Hostel Type, Report Type, and Keyword ────────────

def test_ac2_filter_by_category(client, test_db):
    """
    AC2: Given a resident filters by category, when the filter is applied,
         then matching reports are displayed.
    """
    student1 = test_db["student1"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by 'Keys' category
    res_keys = client.get("/api/lost-and-found?item_category=Keys", headers=headers)
    assert res_keys.status_code == 200
    data_keys = res_keys.json()
    assert len(data_keys["reports"]) == 1
    assert data_keys["reports"][0]["item_category"] == "Keys"
    assert data_keys["reports"][0]["item_name"] == "Set of 3 Room Keys on Leather Ring"

    # Filter by 'Electronics' category
    res_elec = client.get("/api/lost-and-found?item_category=Electronics", headers=headers)
    assert res_elec.status_code == 200
    data_elec = res_elec.json()
    assert len(data_elec["reports"]) == 1
    assert data_elec["reports"][0]["item_category"] == "Electronics"


def test_ac2_filter_by_hostel_type(client, test_db):
    """
    AC2: Given a resident filters by hostel type, when the filter is applied,
         then matching reports are displayed.
    """
    student1 = test_db["student1"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by 'Girls Hostel'
    res_girls = client.get("/api/lost-and-found?hostel_type=Girls+Hostel", headers=headers)
    assert res_girls.status_code == 200
    data_girls = res_girls.json()
    assert len(data_girls["reports"]) == 1
    assert data_girls["reports"][0]["hostel_type"] == "Girls Hostel"
    assert data_girls["reports"][0]["item_name"] == "Set of 3 Room Keys on Leather Ring"

    # Filter by 'Boys Hostel'
    res_boys = client.get("/api/lost-and-found?hostel_type=Boys+Hostel", headers=headers)
    assert res_boys.status_code == 200
    data_boys = res_boys.json()
    assert len(data_boys["reports"]) == 2
    for r in data_boys["reports"]:
        assert r["hostel_type"] == "Boys Hostel"


def test_ac2_filter_by_report_type_and_search_keyword(client, test_db):
    """
    AC2: Test filtering by report_type ('Lost' vs 'Found') and keyword search query.
    """
    student1 = test_db["student1"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by report_type='Found'
    res_found = client.get("/api/lost-and-found?report_type=Found", headers=headers)
    assert res_found.status_code == 200
    for r in res_found.json()["reports"]:
        assert r["report_type"] == "Found"

    # Search keyword "Hoodie"
    res_search = client.get("/api/lost-and-found?search=Hoodie", headers=headers)
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert len(data_search["reports"]) == 1
    assert "Hoodie" in data_search["reports"][0]["item_name"]


# ── AC3: Item Details Page Loads with All Relevant Information ────────────────

def test_ac3_item_details_page_loads_with_required_fields(client, test_db):
    """
    AC3: Given a resident opens an item report, when the details page loads,
         then the image, description, location, and report status are shown according to access permissions.
    """
    student1 = test_db["student1"]
    item = test_db["item_active_lost"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/lost-and-found/{item.item_report_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Verify image, description, location, and report status (AC3)
    assert data["item_report_id"] == item.item_report_id
    assert data["image_reference"] == "uploads/lost-and-found/sony_headphones.jpg"
    assert data["description"] == "Black noise-canceling headphones left in study hall."
    assert data["location"] == "Reading Room Desk 12"
    assert data["status"] == "Submitted"
    assert data["hostel_type"] == "Boys Hostel"
    assert data["item_category"] == "Electronics"
    assert data["identifying_details"] == "Serial number SN-778844 on inner headband"
    assert data["reporter_name"] == "Resident Bob"


# ── AC4: Closed/Returned Items Marked as Closed or Excluded from Active Listings

def test_ac4_closed_items_marked_or_removed_from_active_listings(client, test_db):
    """
    AC4: Given an item has been returned or closed, when the listing loads,
         then it is marked as closed or removed from active listings.
    """
    student1 = test_db["student1"]
    token = create_access_token(data={"sub": str(student1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. When hide_closed=true (active listings), Returned/Closed items are excluded
    res_active = client.get("/api/lost-and-found?hide_closed=true", headers=headers)
    assert res_active.status_code == 200
    active_reports = res_active.json()["reports"]
    for r in active_reports:
        assert r["status"] not in ["Returned", "Closed"]

    # 2. When listing all items (hide_closed=false), closed item is present and has status='Returned' and closed_at set
    res_all = client.get("/api/lost-and-found?hide_closed=false", headers=headers)
    assert res_all.status_code == 200
    all_reports = res_all.json()["reports"]
    closed_items = [r for r in all_reports if r["status"] in ["Returned", "Closed"]]
    assert len(closed_items) >= 1
    assert closed_items[0]["closed_at"] is not None
    assert closed_items[0]["status"] == "Returned"


# ── AC5: Resident Claim Submission Sent to Authorized Staff ───────────────────

def test_ac5_resident_claim_request_sent_to_staff(client, test_db):
    """
    AC5: Given a resident wants to claim an item, when they submit a claim request,
         then the request is sent to authorized staff for verification.
    """
    student1 = test_db["student1"]
    item_found = test_db["item_active_found"]
    warden = test_db["warden"]

    student_token = create_access_token(data={"sub": str(student1.id)})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Resident submits claim request
    claim_payload = {
        "proof_details": "Key ring has a small dent on the brass master key; my room is 302.",
        "claim_notes": "Please contact me at 9876543210. Available between 5-7 PM.",
    }

    claim_res = client.post(
        f"/api/lost-and-found/{item_found.item_report_id}/claim",
        json=claim_payload,
        headers=student_headers,
    )
    assert claim_res.status_code == 200, f"Claim failed: {claim_res.text}"
    claim_data = claim_res.json()

    # Status must be updated to 'Claim Requested' (AC5)
    assert claim_data["status"] == "Claim Requested"

    # Verify status history audit recorded the claim with claimant notes
    warden_token = create_access_token(data={"sub": str(warden.id)})
    warden_headers = {"Authorization": f"Bearer {warden_token}"}

    history_res = client.get(
        f"/api/lost-and-found/{item_found.item_report_id}/history",
        headers=warden_headers,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    latest_event = history[0]
    assert latest_event["to_status"] == "Claim Requested"
    assert latest_event["changed_by_id"] == student1.id
    assert "Resident Bob" in latest_event["reason"]
    assert "Key ring has a small dent" in latest_event["reason"]

    # Authorized staff verifies and closes the claim
    verify_res = client.patch(
        f"/api/lost-and-found/{item_found.item_report_id}/status",
        json={
            "status": "Verified",
            "assigned_staff": "Warden Mike",
            "reason": "Ownership proof verified against hostel registry for Room 302",
        },
        headers=warden_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "Verified"


def test_ac5_cannot_claim_already_closed_item(client, test_db):
    """
    AC5 validation: Attempting to claim an item that is already returned/closed must return 400 Bad Request.
    """
    student1 = test_db["student1"]
    item_closed = test_db["item_closed"]
    student_token = create_access_token(data={"sub": str(student1.id)})
    student_headers = {"Authorization": f"Bearer {student_token}"}

    res = client.post(
        f"/api/lost-and-found/{item_closed.item_report_id}/claim",
        json={"proof_details": "This is mine"},
        headers=student_headers,
    )
    assert res.status_code == 400
    assert "already returned or closed" in res.json()["detail"]


# ── Frontend Component Structure & Contract Verification ─────────────────────

def test_frontend_component_contracts():
    """
    Verify frontend component contracts in LostAndFoundListing.jsx:
    - Search input and category filter dropdown (AC2)
    - Hostel type filter (AC2)
    - Item details view / modal elements (AC3)
    - Active / Hide closed toggle (AC4)
    - Claim submission modal with proof and notes inputs (AC5)
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "LostAndFoundListing.jsx")
    assert os.path.exists(file_path), f"LostAndFoundListing.jsx missing at {file_path}"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # AC1 & AC2: Search and filtering elements
    assert 'id="search-input"' in content, "search-input missing"
    assert 'id="category-select"' in content, "category-select missing"
    assert 'id="hostel-type-select"' in content, "hostel-type-select missing"
    assert 'id="report-type-filter"' in content, "report-type-filter missing"

    # AC3: Details modal elements
    assert 'id="item-details-modal"' in content, "item-details-modal missing"
    assert 'id="details-item-name"' in content, "details-item-name missing"
    assert 'id="details-location"' in content, "details-location missing"
    assert 'id="details-description"' in content, "details-description missing"

    # AC4: Hide closed checkbox toggle
    assert 'id="hide-closed-checkbox"' in content, "hide-closed-checkbox missing"

    # AC5: Claim modal and submission button
    assert 'id="claim-modal"' in content, "claim-modal missing"
    assert 'id="claim-proof-details"' in content, "claim-proof-details missing"
    assert 'id="submit-claim-btn"' in content, "submit-claim-btn missing"
    assert 'id="btn-claim-item"' in content, "btn-claim-item missing"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
