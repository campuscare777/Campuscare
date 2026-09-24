"""
HOSTELCARE-F004-DB-001: Lost and Found Database Verification Test
Story: As the system, I need to persist missing and found item reports, so that items can be tracked until they are returned or closed.

AC1: Given an item report is created, when saved, then all relevant details are retrievable.
AC2: Given a staff member updates an item status, when saved, then the new status is recorded.
AC3: Given an item is returned, when the report is closed, then the return/closure timestamp is saved.
"""

import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.session import Base
from app.models.user import User
from app.models.lost_and_found import LostAndFoundItemReport, LostAndFoundStatusHistory
from app.services.lost_and_found_service import LostAndFoundService, ALLOWED_STATUSES
from app.schemas.lost_and_found import LostAndFoundCreate, LostAndFoundStatusUpdate
from app.main import app as fastapi_app
from app.services.auth_service import create_access_token


def test_db_schema_and_ac_direct():
    """AC1, AC2, AC3 Direct SQLAlchemy Test on in-memory SQLite DB."""
    print("\n[SUITE] PART 1: Direct DB Schema & AC Verification (In-Memory SQLite)")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Verify Table Existence
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "lost_and_found_reports" in tables, f"'lost_and_found_reports' table missing! Found: {tables}"
    assert "lost_and_found_status_history" in tables, f"'lost_and_found_status_history' table missing! Found: {tables}"
    print("[PASS] Tables 'lost_and_found_reports' & 'lost_and_found_status_history' exist in database schema")

    # 2. Verify Field Specifications
    columns = {c["name"]: c for c in inspector.get_columns("lost_and_found_reports")}
    suggested_fields = [
        "item_report_id",
        "reporter_id",
        "report_type",
        "item_category",
        "item_name",
        "description",
        "image_reference",
        "hostel_type",
        "location",
        "date_lost_or_found",
        "identifying_details",
        "status",
        "assigned_staff",
        "created_at",
        "updated_at",
        "closed_at",
    ]
    for field in suggested_fields:
        assert field in columns, f"Suggested field '{field}' is MISSING from lost_and_found_reports table!"
    print(f"[PASS] All {len(suggested_fields)} suggested fields present in lost_and_found_reports schema")

    # 3. Seed test reporter user
    user = User(
        username="reporter_student",
        email="reporter@campus.edu",
        hashed_password="hashedpassword",
        full_name="Reporter Student",
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # AC1: Given an item report is created, when saved, then all relevant details are retrievable.
    now_dt = datetime.utcnow()
    report = LostAndFoundItemReport(
        reporter_id=user.id,
        report_type="Lost",
        item_category="Electronics",
        item_name="Blue Sony Headphones",
        description="Noise-cancelling wireless headphones left in library.",
        image_reference="uploads/lost_headphones.jpg",
        hostel_type="Boys Hostel",
        location="Hostel Block B, Reading Room",
        date_lost_or_found=now_dt,
        identifying_details="Serial No: SN-998811, blue case with custom sticker",
        status="Submitted",
        assigned_staff="Caretaker John",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    assert report.item_report_id is not None and report.item_report_id > 0, "item_report_id not generated"
    assert report.id == report.item_report_id, "id property alias mismatch"

    # Fetch and verify all details retrievable (AC1)
    fetched = db.query(LostAndFoundItemReport).filter(LostAndFoundItemReport.item_report_id == report.item_report_id).first()
    assert fetched is not None, "Report not found after DB persist"
    assert fetched.reporter_id == user.id, "reporter_id mismatch"
    assert fetched.report_type == "Lost", "report_type mismatch"
    assert fetched.item_category == "Electronics", "item_category mismatch"
    assert fetched.item_name == "Blue Sony Headphones", "item_name mismatch"
    assert fetched.description == "Noise-cancelling wireless headphones left in library.", "description mismatch"
    assert fetched.image_reference == "uploads/lost_headphones.jpg", "image_reference mismatch"
    assert fetched.hostel_type == "Boys Hostel", "hostel_type mismatch"
    assert fetched.location == "Hostel Block B, Reading Room", "location mismatch"
    assert fetched.date_lost_or_found == now_dt, "date_lost_or_found mismatch"
    assert fetched.identifying_details == "Serial No: SN-998811, blue case with custom sticker", "identifying_details mismatch"
    assert fetched.status == "Submitted", "status mismatch"
    assert fetched.assigned_staff == "Caretaker John", "assigned_staff mismatch"
    assert fetched.created_at is not None, "created_at missing"
    assert fetched.updated_at is not None, "updated_at missing"
    assert fetched.closed_at is None, "closed_at should initially be None"
    print("[PASS] AC1 Direct: All item report fields retrievable intact after DB persist")

    # AC2: Given a staff member updates an item status, when saved, then the new status is recorded.
    service = LostAndFoundService(db)
    all_statuses = [
        "Under Review",
        "Published",
        "Claim Requested",
        "Verified",
        "Returned",
        "Closed",
        "Rejected",
    ]
    for next_status in all_statuses:
        status_update = LostAndFoundStatusUpdate(
            status=next_status,
            assigned_staff="Staff Member Smith",
            reason=f"Transition to {next_status}",
        )
        updated = service.update_status(
            item_report_id=report.item_report_id,
            changed_by_id=user.id,
            payload=status_update,
        )
        assert updated.status == next_status, f"Expected status '{next_status}', got '{updated.status}'"
        assert updated.assigned_staff == "Staff Member Smith"
        
        # Check AC3: Return / Closure timestamp saved on 'Returned' or 'Closed'
        if next_status in ["Returned", "Closed"]:
            assert updated.closed_at is not None, f"AC3 Failed: closed_at not set when status became '{next_status}'"

    print("[PASS] AC2 Direct: Staff status updates successfully recorded through lifecycle")
    print("[PASS] AC3 Direct: Return/Closure timestamp (closed_at) automatically populated and saved")

    # Verify audit history
    history = service.get_status_history(report.item_report_id)
    assert len(history) == len(all_statuses), f"Expected {len(all_statuses)} history records, got {len(history)}"
    print(f"[PASS] Status history audit trail verified ({len(history)} transitions recorded)")

    db.close()


def test_fastapi_endpoints_roundtrip():
    """AC1, AC2, AC3 via FastAPI TestClient round-trip HTTP endpoints."""
    print("\n[SUITE] PART 2: FastAPI HTTP Endpoints Round-Trip Test")

    import app.models  # Ensure all model tables are registered in Base.metadata
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed user
    student = User(username="std101", email="std101@campus.edu", hashed_password="pwd", full_name="Student 101", role="student")
    staff = User(username="staff101", email="staff101@campus.edu", hashed_password="pwd", full_name="Staff 101", role="admin")
    db.add_all([student, staff])
    db.commit()
    db.refresh(student)
    db.refresh(staff)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    from app.db.session import get_db
    fastapi_app.dependency_overrides[get_db] = override_get_db

    client = TestClient(fastapi_app)

    # Authenticate student
    token = create_access_token(data={"sub": str(student.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # AC1: Create report via API
    payload = {
        "report_type": "Found",
        "item_category": "Keys",
        "item_name": "Bunch of 3 brass keys with blue keychain",
        "description": "Found near Hostel A mess entrance",
        "image_reference": "uploads/found_keys.png",
        "hostel_type": "Girls Hostel",
        "location": "Hostel A Mess Entrance",
        "date_lost_or_found": "2026-09-24T18:00:00",
        "identifying_details": "Key ring says 'Godrej'",
    }
    response = client.post("/api/lost-and-found", json=payload, headers=headers)
    assert response.status_code == 201, f"Create report failed: {response.text}"
    data = response.json()

    assert data["item_report_id"] > 0, "item_report_id missing in API response"
    assert data["report_type"] == "Found"
    assert data["item_category"] == "Keys"
    assert data["item_name"] == payload["item_name"]
    assert data["status"] == "Submitted"
    assert data["closed_at"] is None
    item_report_id = data["item_report_id"]
    print(f"[PASS] AC1 HTTP: Created item report #{item_report_id} with status='Submitted'")

    # AC1: Retrieve report by ID
    get_res = client.get(f"/api/lost-and-found/{item_report_id}", headers=headers)
    assert get_res.status_code == 200, f"GET report failed: {get_res.text}"
    fetched = get_res.json()
    assert fetched["item_report_id"] == item_report_id
    assert fetched["identifying_details"] == payload["identifying_details"]
    assert fetched["location"] == payload["location"]
    print(f"[PASS] AC1 HTTP: Retrievable intact by ID #{item_report_id}")

    # AC2: Staff updates item status to 'Under Review', then 'Verified'
    staff_token = create_access_token(data={"sub": str(staff.id)})
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    patch_res = client.patch(
        f"/api/lost-and-found/{item_report_id}/status",
        json={"status": "Under Review", "assigned_staff": "Security Warden"},
        headers=staff_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Under Review"
    assert patch_res.json()["assigned_staff"] == "Security Warden"
    print(f"[PASS] AC2 HTTP: Status updated to 'Under Review'")

    # AC3: Close / Return item report and verify closure timestamp
    close_res = client.patch(
        f"/api/lost-and-found/{item_report_id}/status",
        json={"status": "Returned", "reason": "Item handed over to verified owner"},
        headers=staff_headers,
    )
    assert close_res.status_code == 200
    closed_data = close_res.json()
    assert closed_data["status"] == "Returned"
    assert closed_data["closed_at"] is not None, "AC3 HTTP Failed: closed_at timestamp is None on Returned"
    print(f"[PASS] AC3 HTTP: Item status set to 'Returned' and closed_at timestamp '{closed_data['closed_at']}' saved")

    # List reports filtering
    list_res = client.get("/api/lost-and-found?report_type=Found&status=Returned", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    print("[PASS] HTTP List filtering verified")

    fastapi_app.dependency_overrides.clear()
    db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("HOSTELCARE-F004-DB-001: Lost and Found Database Test Suite")
    print("=" * 70)
    test_db_schema_and_ac_direct()
    test_fastapi_endpoints_roundtrip()
    print("=" * 70)
    print("ALL ACs & TESTS PASSED FOR HOSTELCARE-F004-DB-001!")
    print("=" * 70)
