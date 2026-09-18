import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def safe_urlopen(req, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req)
        except (ConnectionResetError, urllib.error.URLError) as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.3)

class APIClient:
    def __init__(self):
        self.token = None

    def _headers(self, extra=None):
        h = {'User-Agent': 'TestClient/1.0', 'Connection': 'close'}
        if self.token:
            h['Authorization'] = f'Bearer {self.token}'
        if extra:
            h.update(extra)
        return h

    def login(self, username, password):
        payload = json.dumps({"username": username, "password": password}).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/login",
            data=payload,
            headers=self._headers({'Content-Type': 'application/json'}),
            method='POST'
        )
        try:
            res = safe_urlopen(req)
            data = json.loads(res.read().decode('utf-8'))
            self.token = data.get("access_token")
            return res.status, data
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                return e.code, json.loads(body)
            except:
                return e.code, body

    def post_multipart(self, path, fields, file_field=None, file_name=None, file_bytes=None, content_type="image/jpeg"):
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = []
        for k, v in fields.items():
            if v is not None:
                body.append(f"--{boundary}".encode('utf-8'))
                body.append(f'Content-Disposition: form-data; name="{k}"'.encode('utf-8'))
                body.append(b"")
                body.append(str(v).encode('utf-8'))
        
        if file_field and file_name and file_bytes is not None:
            body.append(f"--{boundary}".encode('utf-8'))
            body.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"'.encode('utf-8'))
            body.append(f'Content-Type: {content_type}'.encode('utf-8'))
            body.append(b"")
            body.append(file_bytes)

        body.append(f"--{boundary}--".encode('utf-8'))
        body.append(b"")

        payload = b"\r\n".join(body)
        headers = self._headers({'Content-Type': f'multipart/form-data; boundary={boundary}'})
        req = urllib.request.Request(f"{BASE_URL}{path}", data=payload, headers=headers, method='POST')
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body_err = e.read().decode('utf-8')
            try:
                return e.code, json.loads(body_err)
            except:
                return e.code, body_err

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_scrum01_ui001():
    log("Starting SCRUM05-F001-UI-001 Acceptance Criteria Verification...")

    student = APIClient()

    # Step 1: Login as student
    code, data = student.login("student1", "student123")
    assert code == 200, f"Login failed: {data}"
    log("Login student1: SUCCESS", "PASS")

    # Step 2: AC2 Test - Submit WITHOUT photo
    log("Testing AC2: Given no photo attached, submission is blocked with validation message...")
    fields_no_photo = {
        "location": "Main Library, 2nd Floor",
        "building": "Library",
        "floor": "2nd Floor"
    }
    code, err_data = student.post_multipart("/api/reports", fields_no_photo)
    assert code == 400, f"Expected 400 for missing photo, got {code}"
    log(f"AC2 PASSED: Backend blocked submission with validation error: '{err_data['detail']}'", "PASS")

    # Step 3: AC1 Test - Submit WITH photo and location
    log("Testing AC1: Given photo uploaded and location selected, report is created with confirmation...")
    fields_valid = {
        "location": "Library Reading Room A",
        "building": "Main Library",
        "floor": "1st Floor",
        "area": "Study Desk #12",
        "description": "Broken chair legs and torn cushion."
    }
    code, report_data = student.post_multipart("/api/reports", fields_valid, "photo", "issue.jpg", b"fake photo binary data")
    assert code == 200, f"Expected 200 for valid report, got {code}: {report_data}"
    assert "id" in report_data and report_data["id"] > 0, "Report ID missing"
    assert report_data["status"] in ["Submitted", "Reported"], f"Unexpected initial status: {report_data['status']}"
    log(f"AC1 PASSED: Created report #{report_data['id']} at '{report_data['location']}' with status '{report_data['status']}'", "PASS")

    log("SCRUM05-F001-UI-001 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!", "SUCCESS")

if __name__ == "__main__":
    test_scrum01_ui001()
