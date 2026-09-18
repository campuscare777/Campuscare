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

    def get(self, path):
        req = urllib.request.Request(f"{BASE_URL}{path}", headers=self._headers())
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body_err = e.read().decode('utf-8')
            try:
                return e.code, json.loads(body_err)
            except:
                return e.code, body_err

    def post_multipart(self, path, fields, file_field="photo", file_name="photo.jpg", file_bytes=b"sample binary content", content_type="image/jpeg"):
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

def test_scrum01_be001():
    log("Starting SCRUM05-F001-BE-001 (Report Creation & Persistence API) Verification...")

    client = APIClient()

    # Step 1: Login
    code, data = client.login("student1", "student123")
    assert code == 200, f"Login failed: {data}"
    log("Login student1: SUCCESS", "PASS")

    # Step 2: Submit report payload (AC1)
    fields = {
        "location": "Science Block, Lab 102",
        "building": "Science Block",
        "floor": "1st Floor",
        "area": "Physics Lab",
        "description": "Leaking sink tap in Physics Lab 102."
    }
    code, report_data = client.post_multipart("/api/reports", fields, "photo", "tap.jpg", b"image data bytes")
    assert code == 200, f"Report creation failed with status {code}: {report_data}"
    assert "id" in report_data and report_data["id"] > 0, "Reference ID missing in response"
    assert report_data["status"] == "Submitted", f"Expected status 'Submitted', got '{report_data['status']}'"
    ref_id = report_data["id"]
    log(f"AC1 PASSED: Report created with reference ID #{ref_id} and status '{report_data['status']}'", "PASS")

    # Step 3: Fetch report record by reference ID to verify persistence
    code, fetched_report = client.get(f"/api/reports/{ref_id}")
    assert code == 200, f"Get report by ID failed: {fetched_report}"
    assert fetched_report["id"] == ref_id, "Fetched ID mismatch"
    assert fetched_report["status"] == "Submitted", "Persisted status mismatch"
    assert fetched_report["location"] == fields["location"], "Persisted location mismatch"
    log(f"Database Persistence PASSED: Report #{ref_id} retrieved from DB store successfully", "PASS")

    log("SCRUM05-F001-BE-001 ALL ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!", "SUCCESS")

if __name__ == "__main__":
    test_scrum01_be001()
