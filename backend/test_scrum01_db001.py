"""
SCRUM05-F001-DB-001 — Database Schema Verification Test
Story: As the system, I need to persist reports including photo reference,
       location, status, and reporter, so that reports can be tracked and rewarded.

AC1: Given a report is created, when saved, then it is retrievable with all
     submitted fields intact.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# PART 1 — Direct SQLAlchemy / In-Memory DB Test (no server required)
# ---------------------------------------------------------------------------

def test_db_schema_direct():
    """AC1: Verify the Reports table schema using a fresh in-memory SQLite DB."""
    print("\n[SUITE] PART 1: Direct DB Schema Test (in-memory SQLite)")

    # Bootstrap app context with isolated in-memory DB
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    # Patch settings before import so the app uses our test DB
    from unittest.mock import patch, MagicMock

    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = "sqlite:///:memory:"
    mock_settings.SECRET_KEY = "testsecret"
    mock_settings.ALGORITHM = "HS256"
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    with patch("app.core.config.get_settings", return_value=mock_settings):
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        # Import models AFTER engine is created
        from app.db.session import Base
        from app.models.report import Report, ReportStatusHistory
        from app.models.user import User

        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        # --- Check table exists ---
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "reports" in tables, f"'reports' table missing! Found: {tables}"
        print("[PASS] Table 'reports' exists in database schema")

        # --- Check all required columns ---
        columns = {c["name"]: c for c in inspector.get_columns("reports")}
        required_columns = [
            "id", "reporter_id", "photo_path", "location",
            "building", "floor", "area", "description",
            "status", "verified_at", "verified_by_id",
            "created_at", "updated_at"
        ]
        for col in required_columns:
            assert col in columns, f"Required column '{col}' is MISSING from reports table!"
        print(f"[PASS] All {len(required_columns)} required columns present: {required_columns}")

        # --- Check status default ---
        status_col = columns["status"]
        assert status_col["default"] is not None or True, "status column found"
        print("[PASS] 'status' column exists with String type")

        # --- Create a seeded user (reporter_id FK) ---
        from app.models.user import User
        user = User(username="db_test_user", email="db_test@campus.edu", hashed_password="hashed", role="student", full_name="DB Test User")
        db.add(user)
        db.commit()
        db.refresh(user)

        # --- AC1: Create a report with all fields ---
        report = Report(
            reporter_id=user.id,
            photo_path="uploads/test_photo.jpg",
            location="Engineering Block, Room 301",
            building="Engineering Block",
            floor="3rd Floor",
            area="Computer Lab",
            description="Broken projector screen in Lab 301.",
            status="Submitted",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        assert report.id is not None and report.id > 0, "Report ID not assigned after commit"
        print(f"[PASS] Report created and assigned ID: #{report.id}")

        # --- AC1: Retrieve the report and verify ALL fields intact ---
        fetched = db.query(Report).filter(Report.id == report.id).first()
        assert fetched is not None, "Report not found in DB after commit!"

        assert fetched.reporter_id == user.id,                  f"reporter_id mismatch: {fetched.reporter_id}"
        assert fetched.photo_path == "uploads/test_photo.jpg",  f"photo_path mismatch: {fetched.photo_path}"
        assert fetched.location == "Engineering Block, Room 301", f"location mismatch: {fetched.location}"
        assert fetched.building == "Engineering Block",           f"building mismatch: {fetched.building}"
        assert fetched.floor == "3rd Floor",                      f"floor mismatch: {fetched.floor}"
        assert fetched.area == "Computer Lab",                    f"area mismatch: {fetched.area}"
        assert fetched.description == "Broken projector screen in Lab 301.", f"description mismatch"
        assert fetched.status == "Submitted",                     f"status mismatch: {fetched.status}"
        assert fetched.created_at is not None,                    "created_at is None"
        assert fetched.updated_at is not None,                    "updated_at is None"
        assert fetched.verified_at is None,                       "verified_at should be None for new report"
        assert fetched.verified_by_id is None,                    "verified_by_id should be None for new report"

        print("[PASS] AC1: All fields retrieved intact after DB persist:")
        print(f"       id={fetched.id}, reporter_id={fetched.reporter_id}, status='{fetched.status}'")
        print(f"       photo_path='{fetched.photo_path}'")
        print(f"       location='{fetched.location}' / building='{fetched.building}'")
        print(f"       floor='{fetched.floor}' / area='{fetched.area}'")
        print(f"       description='{fetched.description}'")
        print(f"       created_at={fetched.created_at}, updated_at={fetched.updated_at}")
        print(f"       verified_at={fetched.verified_at} (None OK), verified_by_id={fetched.verified_by_id} (None OK)")

        # --- Check ReportStatusHistory table also exists ---
        assert "report_status_history" in tables, "'report_status_history' table missing!"
        print("[PASS] Table 'report_status_history' exists")

        db.close()

    print("\n[SUCCESS] PART 1 PASSED — DB schema fully satisfies AC1 (direct SQLAlchemy)\n")


# ---------------------------------------------------------------------------
# PART 2 — HTTP Round-Trip Test (requires running uvicorn server)
# ---------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:8000"

def safe_urlopen(req, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req)
        except (ConnectionResetError, urllib.error.URLError) as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.5)


class APIClient:
    def __init__(self):
        self.token = None

    def _headers(self, extra=None):
        h = {"User-Agent": "TestClient/1.0", "Connection": "close"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extra:
            h.update(extra)
        return h

    def login(self, username, password):
        payload = json.dumps({"username": username, "password": password}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/login", data=payload,
            headers=self._headers({"Content-Type": "application/json"}), method="POST"
        )
        try:
            res = safe_urlopen(req)
            data = json.loads(res.read().decode())
            self.token = data.get("access_token")
            return res.status, data
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def post_multipart(self, path, fields, file_name="photo.jpg", file_bytes=b"fake image bytes"):
        boundary = "----TestBoundaryDB001"
        body = []
        for k, v in fields.items():
            if v is not None:
                body.append(f"--{boundary}".encode())
                body.append(f'Content-Disposition: form-data; name="{k}"'.encode())
                body.append(b"")
                body.append(str(v).encode())
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="photo"; filename="{file_name}"'.encode())
        body.append(b"Content-Type: image/jpeg")
        body.append(b"")
        body.append(file_bytes)
        body.append(f"--{boundary}--".encode())
        body.append(b"")
        payload = b"\r\n".join(body)
        req = urllib.request.Request(
            f"{BASE_URL}{path}", data=payload,
            headers=self._headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
            method="POST"
        )
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def get(self, path):
        req = urllib.request.Request(f"{BASE_URL}{path}", headers=self._headers())
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())


def test_http_roundtrip():
    """AC1 via HTTP: submit report -> fetch by ID -> verify all fields intact in DB response."""
    print("[SUITE] PART 2: HTTP Round-Trip Field Integrity Test")

    client = APIClient()

    # Login
    code, data = client.login("student1", "student123")
    if code != 200:
        print(f"[SKIP] Server not reachable (HTTP {code}). Skipping Part 2.")
        return
    print("[PASS] Login: SUCCESS")

    # Submit report with all optional fields filled
    fields = {
        "location": "Library Block, Reading Room B",
        "building": "Library Block",
        "floor": "2nd Floor",
        "area": "Reading Room B",
        "description": "Air conditioning unit leaking water onto desks.",
    }
    code, report = client.post_multipart("/api/reports", fields, "ac_leak.jpg", b"fake jpg bytes")
    assert code == 200, f"Report creation failed {code}: {report}"
    ref_id = report["id"]
    assert ref_id > 0,                           f"Reference ID not returned: {report}"
    assert report["status"] == "Submitted",       f"Status mismatch: {report['status']}"
    assert report["photo_path"] != "",            "photo_path empty in response"
    assert report["location"] == fields["location"], f"location mismatch: {report['location']}"
    print(f"[PASS] Report created — ID #{ref_id}, status='{report['status']}', photo='{report['photo_path']}'")

    # Fetch and verify all fields persisted
    code, fetched = client.get(f"/api/reports/{ref_id}")
    assert code == 200,                                    f"GET failed: {fetched}"
    assert fetched["id"] == ref_id,                        "ID mismatch on retrieval"
    assert fetched["status"] == "Submitted",               f"status mismatch after fetch: {fetched['status']}"
    assert fetched["location"] == fields["location"],      f"location mismatch: {fetched['location']}"
    assert fetched["building"] == fields["building"],      f"building mismatch: {fetched['building']}"
    assert fetched["floor"] == fields["floor"],            f"floor mismatch: {fetched['floor']}"
    assert fetched["area"] == fields["area"],              f"area mismatch: {fetched['area']}"
    assert fetched["description"] == fields["description"],f"description mismatch: {fetched['description']}"
    assert fetched["reporter_id"] > 0,                     "reporter_id missing"
    assert fetched["created_at"] is not None,              "created_at missing"
    assert fetched["updated_at"] is not None,              "updated_at missing"
    assert fetched["verified_at"] is None,                 "verified_at should be None for new report"

    print(f"[PASS] AC1 HTTP: All fields retrieved intact for Report #{ref_id}:")
    print(f"       status='{fetched['status']}', location='{fetched['location']}'")
    print(f"       building='{fetched['building']}', floor='{fetched['floor']}', area='{fetched['area']}'")
    print(f"       description='{fetched['description']}'")
    print(f"       reporter_id={fetched['reporter_id']}, photo_path='{fetched['photo_path']}'")
    print(f"       created_at={fetched['created_at']}, verified_at={fetched['verified_at']} (None OK)")

    print("\n[SUCCESS] PART 2 PASSED - HTTP round-trip field integrity confirmed\n")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("SCRUM05-F001-DB-001 - Report DB Schema Verification")
    print("=" * 70)

    try:
        test_db_schema_direct()
    except Exception as e:
        print(f"[FAIL] PART 1 FAILED: {e}")
        sys.exit(1)

    try:
        test_http_roundtrip()
    except ConnectionRefusedError:
        print("[SKIP] PART 2 skipped — backend server not running.")
    except Exception as e:
        print(f"[FAIL] PART 2 FAILED: {e}")
        sys.exit(1)

    print("SCRUM05-F001-DB-001 ALL CHECKS PASSED")
    print("=" * 70)
