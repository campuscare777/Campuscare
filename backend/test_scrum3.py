import urllib.request
import urllib.parse
import json
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def safe_urlopen(req, max_retries=3):
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

    def post_multipart(self, path, fields, file_field, file_name, file_bytes, content_type="image/jpeg"):
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = []
        for k, v in fields.items():
            if v is not None:
                body.append(f"--{boundary}".encode('utf-8'))
                body.append(f'Content-Disposition: form-data; name="{k}"'.encode('utf-8'))
                body.append(b"")
                body.append(str(v).encode('utf-8'))
        
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

    def patch_json(self, path, json_data=None):
        payload = json.dumps(json_data).encode('utf-8') if json_data else b""
        headers = self._headers({'Content-Type': 'application/json'})
        req = urllib.request.Request(f"{BASE_URL}{path}", data=payload, headers=headers, method='PATCH')
        try:
            res = safe_urlopen(req)
            return res.status, json.loads(res.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body_err = e.read().decode('utf-8')
            try:
                return e.code, json.loads(body_err)
            except:
                return e.code, body_err

    def post_json(self, path, json_data=None):
        payload = json.dumps(json_data).encode('utf-8') if json_data else b""
        headers = self._headers({'Content-Type': 'application/json'})
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

def test_scrum3():
    log("Starting Scrum 3 (SCRUM05-F003: Green Tokens & Rewards) Automated Test Suite...")

    student = APIClient()
    maint = APIClient()

    # Step 1: Login as student1
    code, data = student.login("student1", "student123")
    assert code == 200, f"Login student1 failed: {data}"
    log("Login student1: SUCCESS", "PASS")

    # Step 2: Get initial balance
    code, balance_data = student.get("/api/tokens/balance")
    assert code == 200, f"Get balance failed: {balance_data}"
    initial_balance = balance_data["balance"]
    log(f"Initial student balance: {initial_balance} tokens", "PASS")

    # Step 3: Create report
    fields = {
        "location": "Hostel Block A, Washroom 204",
        "building": "Hostel A",
        "floor": "2nd Floor",
        "area": "Washroom",
        "description": "Scrum 3 test issue for token awarding"
    }
    code, report_data = student.post_multipart("/api/reports", fields, "photo", "test.jpg", b"fake photo content")
    assert code == 200, f"Create report failed: {report_data}"
    report_id = report_data["id"]
    log(f"Created report #{report_id} with status '{report_data['status']}'", "PASS")

    # Step 4: Login as maintenance1
    code, data = maint.login("maintenance1", "maint123")
    assert code == 200, f"Login maintenance1 failed: {data}"
    log("Login maintenance1: SUCCESS", "PASS")

    # Step 5: Verify report
    code, verify_data = maint.patch_json(f"/api/reports/{report_id}/verify", {"reason": "Verified for Scrum 3"})
    assert code == 200, f"Verify report failed: {verify_data}"
    log(f"Verified report #{report_id}", "PASS")

    # Step 6: Verify balance increased by 10 tokens
    code, balance_data = student.get("/api/tokens/balance")
    assert code == 200, "Get balance failed"
    new_balance = balance_data["balance"]
    assert new_balance == initial_balance + 10, f"Expected {initial_balance + 10}, got {new_balance}"
    log(f"Student balance updated: {new_balance} tokens (+10)", "PASS")

    # Step 7: Idempotency check
    code, verify_data2 = maint.patch_json(f"/api/reports/{report_id}/verify", {"reason": "Second verify call"})
    assert code == 200, "Second verify failed"
    code, balance_data2 = student.get("/api/tokens/balance")
    assert balance_data2["balance"] == new_balance, "Idempotency failed: tokens awarded twice!"
    log("Idempotency verified: duplicate report verification did not award extra tokens", "PASS")

    # Step 8: Get rewards catalog
    code, rewards = student.get("/api/rewards")
    assert code == 200 and len(rewards) > 0, f"List rewards failed: {rewards}"
    log(f"Fetched {len(rewards)} catalog rewards", "PASS")

    # Step 9: Over-redemption rule check
    expensive_reward = next((r for r in rewards if r["token_cost"] > new_balance), None)
    if expensive_reward:
        code, err_data = student.post_json(f"/api/rewards/{expensive_reward['id']}/redeem")
        assert code == 400, f"Expected 400 for insufficient balance, got {code}"
        log(f"Insufficient balance rule enforced: '{err_data['detail']}'", "PASS")

    # Step 10: Redeem an affordable reward
    affordable_reward = next((r for r in rewards if r["token_cost"] <= new_balance), None)
    if affordable_reward:
        code, redeem_data = student.post_json(f"/api/rewards/{affordable_reward['id']}/redeem")
        assert code == 200, f"Redeem reward failed: {redeem_data}"
        log(f"Redeemed reward '{redeem_data['reward_name']}': remaining balance {redeem_data['remaining_balance']} tokens", "PASS")

    # Step 11: Transaction history check
    code, history_data = student.get("/api/tokens/history")
    assert code == 200 and len(history_data["transactions"]) >= 1, "History check failed"
    log(f"Token history verified: {len(history_data['transactions'])} transactions recorded", "PASS")

    log("SCRUM 3 ALL TESTS PASSED SUCCESSFULLY!", "SUCCESS")

if __name__ == "__main__":
    test_scrum3()
