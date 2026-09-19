"""
SCRUM05-F002-UI-002: Student Status Tracking & 'My Reports' Acceptance Test
Story: As a student, I want to track the status of the issues I reported, so that I know when they are resolved.

Acceptance Criteria:
AC1. Given a student opens 'My Reports', when the list loads, then their reports and current statuses are shown.
"""

import json
import sys
import urllib.request
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8000"


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
            return res.status, data
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def post_multipart(self, path, fields, file_name="photo.jpg", file_bytes=b"fake bytes"):
        boundary = "----F002UI002Boundary"
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

    def get(self, path, params=None):
        url = f"{BASE_URL}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query:
                url = f"{url}?{query}"
        req = urllib.request.Request(url, headers=self._headers())
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


def log(msg, level="INFO"):
    print(f"[{level}] {msg}")


def test_scrum02_ui002():
    log("Starting SCRUM05-F002-UI-002 ('My Reports' Status Tracking) Verification...")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # Step 1: Student 1 logs in
    # -----------------------------------------------------------------------
    student1 = APIClient()
    code, data = student1.login("student1", "student123")
    assert code == 200, f"Student1 login failed: {code} {data}"
    log("Student 1 ('student1') login: SUCCESS", "PASS")

    # -----------------------------------------------------------------------
    # Step 2: Student 1 submits a maintenance report
    # -----------------------------------------------------------------------
    report_fields = {
        "location": "Mechanical Workshop, Lathe Station 4",
        "building": "Engineering Block",
        "floor": "Ground Floor",
        "area": "Workshop Area B",
        "description": "Lathe motor making abnormal grinding noise and vibrating excessively.",
    }
    code, report = student1.post_multipart("/api/reports", report_fields, "lathe_issue.jpg", b"image data")
    assert code == 200, f"Report creation failed: {code} {report}"
    report_id = report["id"]
    initial_status = report["status"]
    assert initial_status in ["Submitted", "Reported"], f"Expected initial status Submitted/Reported, got '{initial_status}'"
    log(f"Student 1 submitted Report #{report_id} with initial status: '{initial_status}'", "PASS")

    # -----------------------------------------------------------------------
    # Step 3: AC1 - Student opens 'My Reports' -> list loads with reports and current statuses
    # -----------------------------------------------------------------------
    code, my_reports = student1.get("/api/reports")
    assert code == 200, f"Failed to fetch My Reports: {code} {my_reports}"
    reports_list = my_reports.get("reports", [])
    assert len(reports_list) > 0, "AC1 FAIL: 'My Reports' returned empty list for student who submitted reports"
    
    # Locate the newly created report in the list
    matching = [r for r in reports_list if r["id"] == report_id]
    assert len(matching) == 1, f"AC1 FAIL: Report #{report_id} not found in student's My Reports list"
    my_report = matching[0]

    # Verify report fields and current status are visible
    assert my_report["status"] == initial_status, f"AC1 FAIL: Status mismatch in list view. Expected '{initial_status}', got '{my_report['status']}'"
    assert my_report["location"] == report_fields["location"], f"AC1 FAIL: Location mismatch in list view: {my_report['location']}"
    assert my_report["building"] == report_fields["building"], f"AC1 FAIL: Building mismatch in list view: {my_report['building']}"
    assert "photo_path" in my_report and my_report["photo_path"], "AC1 FAIL: Photo reference missing in report summary"
    log(f"AC1 PASSED (Initial List View): Report #{report_id} correctly displayed in 'My Reports' with status '{my_report['status']}'", "PASS")

    # -----------------------------------------------------------------------
    # Step 4: Verify Student Data Isolation (Student 2 cannot see Student 1's report)
    # -----------------------------------------------------------------------
    student2 = APIClient()
    code, _ = student2.login("student2", "student123")
    if code == 200:
        code, student2_reports = student2.get("/api/reports")
        assert code == 200, "Student 2 fetch reports failed"
        student2_ids = [r["id"] for r in student2_reports.get("reports", [])]
        assert report_id not in student2_ids, f"Data Isolation FAIL: Student 2 can see Student 1's report #{report_id}"
        log("Student data isolation verified: Student 2 cannot access Student 1's reports", "PASS")

    # -----------------------------------------------------------------------
    # Step 5: Staff verifies and resolves the report
    # -----------------------------------------------------------------------
    staff = APIClient()
    code, _ = staff.login("maintenance1", "maint123")
    if code != 200:
        code, _ = staff.login("admin", "admin123")
    assert code == 200, "Staff login failed"

    # Verify report
    code, verified = staff.patch(f"/api/reports/{report_id}/verify", {"reason": "Technician confirmed faulty bearing"})
    assert code == 200, f"Verify failed: {verified}"
    log(f"Staff marked Report #{report_id} as 'Verified'", "PASS")

    # Set In Progress
    code, in_prog = staff.patch(f"/api/reports/{report_id}/status", {"status": "In Progress", "reason": "Replacement motor ordered"})
    assert code == 200, f"In Progress failed: {in_prog}"
    log(f"Staff updated Report #{report_id} to 'In Progress'", "PASS")

    # Set Resolved
    code, resolved = staff.patch(f"/api/reports/{report_id}/status", {"status": "Resolved", "reason": "New motor installed and tested operational"})
    assert code == 200, f"Resolved failed: {resolved}"
    log(f"Staff updated Report #{report_id} to 'Resolved'", "PASS")

    # -----------------------------------------------------------------------
    # Step 6: AC1 - Student checks 'My Reports' again -> status reflects 'Resolved'
    # -----------------------------------------------------------------------
    code, refreshed_reports = student1.get("/api/reports")
    assert code == 200, f"Failed to refresh My Reports: {code}"
    matching_refreshed = [r for r in refreshed_reports.get("reports", []) if r["id"] == report_id]
    assert len(matching_refreshed) == 1, f"Report #{report_id} disappeared from My Reports"
    updated_report = matching_refreshed[0]

    assert updated_report["status"] == "Resolved", f"AC1 FAIL: Expected status 'Resolved' in student's list, got '{updated_report['status']}'"
    log(f"AC1 PASSED (Updated Status in List): Student's My Reports list reflects updated status: '{updated_report['status']}'", "PASS")

    # Check detail view
    code, detail = student1.get(f"/api/reports/{report_id}")
    assert code == 200, f"Detail fetch failed: {code}"
    assert detail["status"] == "Resolved", f"AC1 FAIL: Detail view status is not Resolved: {detail['status']}"
    assert detail["verified_at"] is not None, "AC1 FAIL: verified_at timestamp missing in detail view"
    log(f"AC1 PASSED (Detail View): Report #{report_id} detail confirmed with status='{detail['status']}' and verified_at timestamp", "PASS")

    # -----------------------------------------------------------------------
    # Step 7: Check Student Status Progression History
    # -----------------------------------------------------------------------
    code, history = student1.get(f"/api/reports/{report_id}/history")
    assert code == 200, f"Failed to fetch history: {code}"
    to_statuses = [h["to_status"] for h in history]
    assert "Verified" in to_statuses, f"Expected Verified in history, got: {to_statuses}"
    assert "In Progress" in to_statuses, f"Expected In Progress in history, got: {to_statuses}"
    assert "Resolved" in to_statuses, f"Expected Resolved in history, got: {to_statuses}"
    log(f"AC1 PASSED (Status History): Student can inspect full status progression: {to_statuses}", "PASS")

    print("=" * 70)
    log("SCRUM05-F002-UI-002 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!", "SUCCESS")
    log("AC1: Student opens 'My Reports' -> reports & real-time statuses displayed accurately", "SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_scrum02_ui002()
    except (ConnectionRefusedError, urllib.error.URLError):
        print("\n[FAIL] Backend server is not running!")
        print("[ACTION] Please start the backend in a separate terminal: uvicorn app.main:app --reload")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
