"""
HOSTELCARE-F004-UI-004: Item Claim and Verification Test Suite

User Story:
  As a resident, I want to submit a claim for a found item, so that authorized
  staff can verify whether it belongs to me.

Acceptance Criteria:
  AC1: Given a resident selects a found item, when they click Claim,
       then a claim form is displayed.
  AC2: Given a resident provides identifying information, when the claim is submitted,
       then a claim request is created.
  AC3: Given authorized staff review a claim, when they approve it,
       then the claim status changes to 'Verified'.
  AC4: Given a claim is rejected, when staff enter a reason,
       then the reason is stored and shown to the claimant.
  AC5: Given an item is handed over, when staff confirm the handover,
       then the item report status changes to 'Returned'.

Definition of Done:
  Claim and verification flow implemented and tested.
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
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory, LostAndFoundClaim
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

    # 1. Seed users: 2 student residents and 1 warden staff
    resident_bob = User(
        username="resident_bob",
        email="bob@campus.edu",
        hashed_password="hashedpassword",
        full_name="Bob Henderson",
        role="student",
    )
    resident_alice = User(
        username="resident_alice",
        email="alice@campus.edu",
        hashed_password="hashedpassword",
        full_name="Alice Smith",
        role="student",
    )
    warden_mike = User(
        username="warden_mike",
        email="warden@campus.edu",
        hashed_password="hashedpassword",
        full_name="Warden Mike",
        role="warden",
    )
    db.add_all([resident_bob, resident_alice, warden_mike])
    db.commit()
    db.refresh(resident_bob)
    db.refresh(resident_alice)
    db.refresh(warden_mike)

    # 2. Seed a found item (Found report by Alice or caretaker, kept in warden custody)
    found_watch = LostAndFoundItemReport(
        reporter_id=resident_alice.id,
        report_type="Found",
        item_category="Jewellery / Accessories",
        item_name="Silver Fossil Chronograph Watch",
        description="Found on gym locker bench after evening badminton session.",
        image_reference="uploads/lost-and-found/fossil_watch.jpg",
        hostel_type="Boys Hostel",
        location="Hostel Gym Locker Room",
        date_lost_or_found=datetime.utcnow() - timedelta(days=1),
        identifying_details="Custom engraving 'BH 2024' on the rear casing",
        status="Received by Staff",
        assigned_staff="Warden Mike",
    )

    found_calculator = LostAndFoundItemReport(
        reporter_id=resident_bob.id,
        report_type="Found",
        item_category="Electronics",
        item_name="Casio FX-991EX Scientific Calculator",
        description="Left in Room 204 study desk.",
        hostel_type="Boys Hostel",
        location="Study Desk 4",
        status="Published",
    )

    db.add_all([found_watch, found_calculator])
    db.commit()
    db.refresh(found_watch)
    db.refresh(found_calculator)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield {
        "db": db,
        "bob": resident_bob,
        "alice": resident_alice,
        "warden": warden_mike,
        "found_watch": found_watch,
        "found_calculator": found_calculator,
    }

    fastapi_app.dependency_overrides.clear()
    db.close()


@pytest.fixture
def client():
    return TestClient(fastapi_app)


# ── AC1: Claim Form Display & Availability for Found Items ────────────────────

def test_ac1_claim_form_contract_and_availability():
    """
    AC1: Given a resident selects a found item, when they click Claim,
         then a claim form is displayed with identifying information fields.
    """
    frontend_path = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "LostAndFoundListing.jsx"
    )
    assert os.path.exists(frontend_path), f"LostAndFoundListing.jsx not found at {frontend_path}"

    with open(frontend_path, "r", encoding="utf-8") as f:
        content = f.read()

    # AC1: Claim modal container and input fields
    assert 'id="claim-modal"' in content, "claim-modal must exist"
    assert 'id="claim-identifying-info"' in content or 'id="claim-proof-details"' in content
    assert 'id="claim-contact-number"' in content or 'id="claim-notes"' in content
    assert 'id="submit-claim-btn"' in content
    assert 'id="btn-claim-item"' in content


# ── AC2: Submit Claim with Identifying Information Creates Claim Request ───────

def test_ac2_resident_submit_claim_creates_claim_request(client, test_db):
    """
    AC2: Given a resident provides identifying information, when the claim is submitted,
         then a claim request is created.
    """
    bob = test_db["bob"]
    found_watch = test_db["found_watch"]
    bob_token = create_access_token(data={"sub": str(bob.id)})
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    claim_payload = {
        "identifying_info": "Back has an engraving 'BH 2024' with a minor scratch on the 9-hour mark.",
        "contact_number": "+91 9876543210",
        "claim_notes": "I can present the original purchase warranty card from Fossil.",
    }

    res = client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json=claim_payload,
        headers=bob_headers,
    )
    assert res.status_code == 200, f"Claim submission failed: {res.text}"
    report_data = res.json()
    assert report_data["status"] == "Claim Requested"

    # Verify that a claim record was created in the database
    claims_res = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/claims",
        headers=bob_headers,
    )
    assert claims_res.status_code == 200
    claims = claims_res.json()
    assert len(claims) == 1
    claim = claims[0]
    assert claim["item_report_id"] == found_watch.item_report_id
    assert claim["claimant_id"] == bob.id
    assert "BH 2024" in claim["identifying_info"]
    assert claim["contact_number"] == "+91 9876543210"
    assert claim["status"] == "Submitted"


def test_ac2_claim_requires_identifying_information(client, test_db):
    """
    AC2 Validation: Submitting a claim without identifying information is rejected.
    """
    bob = test_db["bob"]
    found_watch = test_db["found_watch"]
    bob_token = create_access_token(data={"sub": str(bob.id)})
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    res = client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "   ", "claim_notes": ""},
        headers=bob_headers,
    )
    assert res.status_code == 400
    assert "identifying information" in res.json()["detail"].lower()


# ── AC3: Staff Reviews & Approves Claim -> Status Changes to 'Verified' ───────

def test_ac3_staff_approves_claim_changes_status_to_verified(client, test_db):
    """
    AC3: Given authorized staff review a claim, when they approve it,
         then the claim status changes to 'Verified'.
    """
    bob = test_db["bob"]
    warden = test_db["warden"]
    found_watch = test_db["found_watch"]

    bob_token = create_access_token(data={"sub": str(bob.id)})
    warden_token = create_access_token(data={"sub": str(warden.id)})

    # Bob submits claim
    client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "Engraving BH 2024 matches my initials and admission year."},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    # Warden fetches claims
    claims = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/claims",
        headers={"Authorization": f"Bearer {warden_token}"},
    ).json()
    claim_id = claims[0]["claim_id"]

    # Staff reviews and approves the claim (AC3)
    approve_res = client.post(
        f"/api/lost-and-found/claims/{claim_id}/verify",
        json={"action": "approve", "notes": "Engraving matches student ID BH-2024."},
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert approve_res.status_code == 200, f"Approval failed: {approve_res.text}"
    approved_claim = approve_res.json()
    assert approved_claim["status"] == "Verified"
    assert approved_claim["verified_by_name"] == "Warden Mike"
    assert approved_claim["verified_at"] is not None

    # Check item report status is now Verified
    item_res = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}",
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert item_res.status_code == 200
    assert item_res.json()["status"] == "Verified"


def test_ac3_unauthorized_user_cannot_verify_claim(client, test_db):
    """
    AC3 Authorization: A non-staff resident cannot verify or approve claims.
    """
    bob = test_db["bob"]
    alice = test_db["alice"]
    found_watch = test_db["found_watch"]

    bob_token = create_access_token(data={"sub": str(bob.id)})
    alice_token = create_access_token(data={"sub": str(alice.id)})

    # Bob submits claim
    client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "Serial number SN-1122"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    claims = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/claims",
        headers={"Authorization": f"Bearer {bob_token}"},
    ).json()
    claim_id = claims[0]["claim_id"]

    # Alice (student) attempts to verify
    res = client.post(
        f"/api/lost-and-found/claims/{claim_id}/verify",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res.status_code == 403


# ── AC4: Claim Rejection with Stored Reason Shown to Claimant ─────────────────

def test_ac4_staff_rejects_claim_with_reason_shown_to_claimant(client, test_db):
    """
    AC4: Given a claim is rejected, when staff enter a reason,
         then the reason is stored and shown to the claimant.
    """
    alice = test_db["alice"]
    warden = test_db["warden"]
    found_calculator = test_db["found_calculator"]

    alice_token = create_access_token(data={"sub": str(alice.id)})
    warden_token = create_access_token(data={"sub": str(warden.id)})

    # Alice claims calculator
    client.post(
        f"/api/lost-and-found/{found_calculator.item_report_id}/claim",
        json={"identifying_info": "It has green tape on the cover"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    claims = client.get(
        f"/api/lost-and-found/{found_calculator.item_report_id}/claims",
        headers={"Authorization": f"Bearer {warden_token}"},
    ).json()
    claim_id = claims[0]["claim_id"]

    # Staff rejects claim and enters reason (AC4)
    rejection_reason = "Tape on the found calculator is red, not green. Serial does not match Alice's department log."
    reject_res = client.post(
        f"/api/lost-and-found/claims/{claim_id}/reject",
        json={"action": "reject", "rejection_reason": rejection_reason},
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert reject_res.status_code == 200, f"Rejection failed: {reject_res.text}"
    rejected_claim = reject_res.json()
    assert rejected_claim["status"] == "Rejected"
    assert rejected_claim["rejection_reason"] == rejection_reason

    # Claimant checks their claims (AC4: reason stored and shown to claimant)
    my_claims_res = client.get(
        "/api/lost-and-found/claims?my_claims=true",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert my_claims_res.status_code == 200
    my_claims = my_claims_res.json()
    matching_claim = next((c for c in my_claims if c["claim_id"] == claim_id), None)
    assert matching_claim is not None
    assert matching_claim["status"] == "Rejected"
    assert matching_claim["rejection_reason"] == rejection_reason


def test_ac4_rejection_requires_mandatory_reason(client, test_db):
    """
    AC4 Validation: Staff must enter a reason when rejecting a claim.
    """
    bob = test_db["bob"]
    warden = test_db["warden"]
    found_watch = test_db["found_watch"]

    bob_token = create_access_token(data={"sub": str(bob.id)})
    warden_token = create_access_token(data={"sub": str(warden.id)})

    client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "Some proof"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    claims = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/claims",
        headers={"Authorization": f"Bearer {warden_token}"},
    ).json()
    claim_id = claims[0]["claim_id"]

    # Attempt rejection without reason
    res = client.post(
        f"/api/lost-and-found/claims/{claim_id}/reject",
        json={"action": "reject", "rejection_reason": "   "},
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert res.status_code == 400
    assert "reason is required" in res.json()["detail"].lower()


# ── AC5: Staff Confirms Handover -> Item Report Status Changes to 'Returned' ──

def test_ac5_item_handover_confirmation_changes_status_to_returned(client, test_db):
    """
    AC5: Given an item is handed over, when staff confirm the handover,
         then the item report status changes to 'Returned'.
    """
    bob = test_db["bob"]
    warden = test_db["warden"]
    found_watch = test_db["found_watch"]

    bob_token = create_access_token(data={"sub": str(bob.id)})
    warden_token = create_access_token(data={"sub": str(warden.id)})

    # Bob claims item
    client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "Engraving BH 2024"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    claims = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/claims",
        headers={"Authorization": f"Bearer {warden_token}"},
    ).json()
    claim_id = claims[0]["claim_id"]

    # Step 1: Staff verifies claim
    client.post(
        f"/api/lost-and-found/claims/{claim_id}/verify",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {warden_token}"},
    )

    # Step 2: Staff confirms handover (AC5)
    handover_res = client.post(
        f"/api/lost-and-found/claims/{claim_id}/handover",
        json={"handover_notes": "Physically handed over at Warden Office Desk after ID card check."},
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert handover_res.status_code == 200, f"Handover failed: {handover_res.text}"
    handover_claim = handover_res.json()
    assert handover_claim["status"] == "Returned"
    assert handover_claim["handed_over_at"] is not None

    # Step 3: Verify item report status changed to 'Returned' and closed_at is set (AC5)
    item_res = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}",
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert item_res.status_code == 200
    item_data = item_res.json()
    assert item_data["status"] == "Returned"
    assert item_data["closed_at"] is not None

    # Verify audit history logged the handover
    history_res = client.get(
        f"/api/lost-and-found/{found_watch.item_report_id}/history",
        headers={"Authorization": f"Bearer {warden_token}"},
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert any(h["to_status"] == "Returned" for h in history)


def test_cannot_claim_already_returned_item(client, test_db):
    """Cannot submit a claim for an item that is already Returned / Closed."""
    bob = test_db["bob"]
    found_watch = test_db["found_watch"]
    bob_token = create_access_token(data={"sub": str(bob.id)})

    # Set item to Returned directly in DB
    found_watch.status = "Returned"
    found_watch.closed_at = datetime.utcnow()
    test_db["db"].commit()

    res = client.post(
        f"/api/lost-and-found/{found_watch.item_report_id}/claim",
        json={"identifying_info": "This watch was mine"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert res.status_code == 400
    assert "already returned or closed" in res.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
