"""
SCRUM05-F002-BE-001: Report Verification & Status Update API Acceptance Test
Story: As the maintenance UI, I want to verify a report and update its status,
       so that the reporting workflow progresses correctly.

Acceptance Criteria:
AC1. Given a valid verification/status request is submitted, when processed,
     then the report's status is updated and a status-history entry is recorded.
"""

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def safe_urlopen(req, max_retries=3):
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
        self.user_id = None

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
            f"{BASE_URL}/api/login",
            data=payload,
            headers=self._headers({"Content-Type": "application/json"}),
            method="POST",
        )
        try:
            res = safe_urlopen(req)
            data = json.loads(res.read().decode())
            self.token = data.get("access_token")
            user_info = data.get("user", {})
            self.user_id = user_info.get("id")
            return res.status, data
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def post_multipart(self, path, fields, file_name="photo.jpg", file_bytes=b"fake bytes"):
        boundary = "----F002BE001Boundary"
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
            f"{BASE_URL}{path}",
            data=payload,
            headers=self._headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
            method="POST",
        )
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def patch(self, path, body=None):
        payload = json.dumps(body or {}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=payload,
            headers=self._headers({"Content-Type": "application/json"}),
            method="PATCH",
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


def log(msg, level="INFO"):
    print(f"[{level}] {msg}")


def test_scrum02_be001():
    log("Starting SCRUM05-F002-BE-001 (Report Verification & Status API) Acceptance Verification...")
    print("=" * 75)

    # -----------------------------------------------------------------------
    # Setup: Student submits a new report
    # -----------------------------------------------------------------------
    student = APIClient()
    code, _ = student.login("student1", "student123")
    assert code == 200, f"Student login failed: {code}"
    log("Student login: SUCCESS", "PASS")

    report_payload = {
        "location": "Electrical Substation, Panel 2B",
        "building": "Engineering Block",
        "floor": "Basement",
        "area": "Substation Room",
        "description": "Main circuit breaker overheating and buzzing abnormally.",
    }
    code, report = student.post_multipart("/api/reports", report_payload, "breaker.jpg", b"fake photo data")
    assert code == 200, f"Report submission failed: {code} {report}"
    report_id = report["id"]
    assert report["status"] == "Submitted", f"Expected initial status 'Submitted', got {report['status']}"
    log(f"Test report #{report_id} created with initial status 'Submitted'", "PASS")

    # -----------------------------------------------------------------------
    # Setup: Maintenance staff logs in
    # -----------------------------------------------------------------------
    staff = APIClient()
    code, data = staff.login("maintenance1", "maint123")
    if code != 200:
        code, data = staff.login("admin", "admin123")
    assert code == 200, f"Staff login failed: {code}"
    staff_id = staff.user_id or data.get("user", {}).get("id")
    log(f"Staff login: SUCCESS (staff_id={staff_id})", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 1: PATCH /api/reports/{id}/verify updates status to 'Verified' & records history
    # -----------------------------------------------------------------------
    log(f"Testing AC1: Verifying Report #{report_id} via PATCH /api/reports/{report_id}/verify...")
    verify_reason = "Visual inspection completed, breaker overheating confirmed"
    code, verified_report = staff.patch(f"/api/reports/{report_id}/verify", {"reason": verify_reason})
    assert code == 200, f"Verify endpoint returned error {code}: {verified_report}"
    assert verified_report["status"] == "Verified", f"AC1 FAIL: Expected 'Verified', got '{verified_report['status']}'"
    assert verified_report["verified_at"] is not None, "AC1 FAIL: verified_at timestamp was not populated"
    assert verified_report["eligible_for_token"] is True, "AC1 FAIL: eligible_for_token is not True"
    log(f"AC1 PASSED: Report #{report_id} status updated to 'Verified', eligible_for_token=True", "PASS")

    # Verify status history recorded for verification
    code, history = staff.get(f"/api/reports/{report_id}/history")
    assert code == 200, f"Failed to fetch history: {code}"
    assert len(history) >= 1, "AC1 FAIL: Status history entry not recorded after verification"
    v_entry = history[0]
    assert v_entry["from_status"] == "Submitted", f"AC1 FAIL: Expected from_status='Submitted', got '{v_entry['from_status']}'"
    assert v_entry["to_status"] == "Verified", f"AC1 FAIL: Expected to_status='Verified', got '{v_entry['to_status']}'"
    assert v_entry["reason"] == verify_reason, f"AC1 FAIL: History reason mismatch: '{v_entry['reason']}'"
    log(f"AC1 PASSED: Status history entry recorded: '{v_entry['from_status']}' -> '{v_entry['to_status']}' (reason: '{v_entry['reason']}')", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 2: PATCH /api/reports/{id}/status updates status to 'In Progress' & records history
    # -----------------------------------------------------------------------
    log(f"Testing AC1: Updating Report #{report_id} to 'In Progress' via PATCH /api/reports/{report_id}/status...")
    progress_reason = "Electrician team dispatched with thermal imaging kit"
    code, progress_report = staff.patch(
        f"/api/reports/{report_id}/status",
        {"status": "In Progress", "reason": progress_reason}
    )
    assert code == 200, f"Status update to In Progress failed {code}: {progress_report}"
    assert progress_report["status"] == "In Progress", f"AC1 FAIL: Expected 'In Progress', got '{progress_report['status']}'"
    log(f"AC1 PASSED: Report #{report_id} status updated to 'In Progress'", "PASS")

    # Verify history recorded
    code, history = staff.get(f"/api/reports/{report_id}/history")
    assert code == 200
    p_entry = [h for h in history if h["to_status"] == "In Progress"]
    assert len(p_entry) == 1, "AC1 FAIL: Status history entry for 'In Progress' not found"
    assert p_entry[0]["from_status"] == "Verified", f"Expected from_status='Verified', got '{p_entry[0]['from_status']}'"
    assert p_entry[0]["reason"] == progress_reason, f"History reason mismatch: '{p_entry[0]['reason']}'"
    log(f"AC1 PASSED: Status history entry recorded: 'Verified' -> 'In Progress'", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 3: PATCH /api/reports/{id}/status updates status to 'Resolved' & records history
    # -----------------------------------------------------------------------
    log(f"Testing AC1: Updating Report #{report_id} to 'Resolved' via PATCH /api/reports/{report_id}/status...")
    resolved_reason = "Circuit breaker replaced, thermal scan normal, load testing passed"
    code, resolved_report = staff.patch(
        f"/api/reports/{report_id}/status",
        {"status": "Resolved", "reason": resolved_reason}
    )
    assert code == 200, f"Status update to Resolved failed {code}: {resolved_report}"
    assert resolved_report["status"] == "Resolved", f"AC1 FAIL: Expected 'Resolved', got '{resolved_report['status']}'"
    log(f"AC1 PASSED: Report #{report_id} status updated to 'Resolved'", "PASS")

    # Verify history recorded
    code, history = staff.get(f"/api/reports/{report_id}/history")
    assert code == 200
    r_entry = [h for h in history if h["to_status"] == "Resolved"]
    assert len(r_entry) == 1, "AC1 FAIL: Status history entry for 'Resolved' not found"
    assert r_entry[0]["from_status"] == "In Progress", f"Expected from_status='In Progress', got '{r_entry[0]['from_status']}'"
    assert r_entry[0]["reason"] == resolved_reason, f"History reason mismatch: '{r_entry[0]['reason']}'"
    log(f"AC1 PASSED: Status history entry recorded: 'In Progress' -> 'Resolved'", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 4: Direct Database Verification (SQLite app.db)
    # -----------------------------------------------------------------------
    log("Verifying database persistence directly from SQLite store...")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Check reports table
        cur.execute("SELECT id, status, verified_at, verified_by_id FROM reports WHERE id = ?", (report_id,))
        row = cur.fetchone()
        assert row is not None, f"Report #{report_id} not found in SQLite reports table"
        assert row[1] == "Resolved", f"DB status mismatch: expected 'Resolved', got '{row[1]}'"
        assert row[2] is not None, "DB verified_at timestamp is NULL"
        log(f"Direct DB reports table verified: id={row[0]}, status='{row[1]}', verified_at={row[2]}", "PASS")

        # Check report_status_history table
        cur.execute(
            "SELECT from_status, to_status, reason, changed_by_id FROM report_status_history WHERE report_id = ? ORDER BY id ASC",
            (report_id,)
        )
        db_history = cur.fetchall()
        assert len(db_history) == 3, f"Expected 3 history records in DB, found {len(db_history)}: {db_history}"
        assert db_history[0][:2] == ("Submitted", "Verified")
        assert db_history[1][:2] == ("Verified", "In Progress")
        assert db_history[2][:2] == ("In Progress", "Resolved")
        conn.close()
        log(f"Direct DB report_status_history verified: all 3 audit entries committed intact", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 5: Authorization Guardrails (Security Verification)
    # -----------------------------------------------------------------------
    log("Verifying authorization guardrails: Students cannot verify or change status...")
    # Student attempts to verify report
    code, resp = student.patch(f"/api/reports/{report_id}/verify", {"reason": "Unauthorized attempt"})
    assert code == 403, f"Security FAIL: Student verify request should return 403, got {code}: {resp}"
    log("Security PASSED: Student verify request blocked with 403 Forbidden", "PASS")

    # Student attempts to update status
    code, resp = student.patch(f"/api/reports/{report_id}/status", {"status": "Verified"})
    assert code == 403, f"Security FAIL: Student status update should return 403, got {code}: {resp}"
    log("Security PASSED: Student status update blocked with 403 Forbidden", "PASS")

    # -----------------------------------------------------------------------
    # AC1 Test 6: Input Validation Guardrails
    # -----------------------------------------------------------------------
    log("Verifying validation guardrails: Empty/invalid status rejected...")
    code, resp = staff.patch(f"/api/reports/{report_id}/status", {"status": ""})
    assert code == 400, f"Expected 400 for empty status, got {code}: {resp}"
    log("Validation PASSED: Empty status rejected with 400 Bad Request", "PASS")

    code, resp = staff.patch(f"/api/reports/{report_id}/status", {"status": "NonExistentStatus"})
    assert code == 400, f"Expected 400 for invalid status, got {code}: {resp}"
    log("Validation PASSED: Invalid status rejected with 400 Bad Request", "PASS")

    code, resp = staff.patch("/api/reports/999999/status", {"status": "In Progress"})
    assert code == 404, f"Expected 404 for non-existent report, got {code}: {resp}"
    log("Validation PASSED: Non-existent report returned 404 Not Found", "PASS")

    print("=" * 75)
    log("SCRUM05-F002-BE-001 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!", "SUCCESS")
    log("AC1: Valid verification/status requests update report status and record status-history entry", "SUCCESS")
    print("=" * 75)


if __name__ == "__main__":
    try:
        test_scrum02_be001()
    except (ConnectionRefusedError, urllib.error.URLError):
        print("\n[FAIL] Backend server is not running!")
        print("[ACTION] Please start the backend in a separate terminal: uvicorn app.main:app --reload")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
