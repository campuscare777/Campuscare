"""HOSTELCARE-F003-UI-003 – redemption verification & fulfilment (AC1-AC4).

Run:  python test_f003_ui003_redemption.py
"""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.token import TokenBalance  # noqa: E402
from app.models.user import User  # noqa: E402

seed()
client = TestClient(app)


def login(username, password):
    r = client.post("/api/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_redemption_verification_flow():
    db = SessionLocal()
    resident = db.query(User).filter(User.username == "resident1").first()
    bal = db.query(TokenBalance).filter(TokenBalance.student_id == resident.id).first()
    bal.balance = 1000
    db.commit()
    db.close()

    student, staff = login("resident1", "resident123"), login("food_staff1", "food123")

    rewards = client.get("/api/rewards", headers=student).json()
    assert rewards
    reward = rewards[0]
    ref = client.post(f"/api/rewards/{reward['id']}/redeem", headers=student).json()["voucher_reference"]

    # AC1 – valid unused reference shows reward details + category
    r = client.get(f"/api/redemptions/{ref.lower()}", headers=staff)
    assert r.status_code == 200
    data = r.json()
    assert data["reward_name"] == reward["name"]
    assert data["reward_category"] == reward["category"]
    assert data["fulfillment_status"] == "Pending"
    assert data["resident_name"]

    # AC4 – routed/displayed to the relevant fulfilment team
    assert data["fulfillment_team"] == {
        "Canteen": "Canteen Team", "Laundry": "Laundry Team", "Hostel Stores": "Hostel Stores Team",
    }[reward["category"]]

    # residents cannot verify vouchers
    assert client.get(f"/api/redemptions/{ref}", headers=student).status_code == 403

    # AC3 – confirm -> Fulfilled
    r = client.patch(f"/api/redemptions/{ref}/fulfill", headers=staff)
    assert r.status_code == 200
    assert client.get(f"/api/redemptions/{ref}", headers=staff).json()["fulfillment_status"] == "Fulfilled"

    # AC2 – re-use of fulfilled reference is blocked
    r = client.patch(f"/api/redemptions/{ref}/fulfill", headers=staff)
    assert r.status_code == 400 and "already been fulfilled" in r.json()["detail"]

    # unknown reference
    assert client.get("/api/redemptions/NOPE", headers=staff).status_code == 404


if __name__ == "__main__":
    test_redemption_verification_flow()
    print("ALL AC1-AC4 CHECKS PASSED")
