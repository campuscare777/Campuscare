"""
HOSTELCARE-F003-UI-004: Admin Reward Management – pytest test suite.

Acceptance criteria verified:
  AC1 – Authorized admin can list all rewards (including inactive)
  AC2 – Admin can create a reward with valid details
  AC3 – Admin can update token cost and availability
  AC4 – Unauthorized resident (and unauthenticated user) is denied access (403 / 401)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.services.auth_service import hash_password
from app.models.user import User
from app.models.reward import RewardCatalogItem

# ─────────────────────────────────────────────────────────────────────────────
# In-memory SQLite test database setup
# ─────────────────────────────────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_f003_ui004.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create tables, seed test users + one existing reward, then clean up."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Admin user
        db.add(User(
            username="test_admin",
            email="test_admin@test.edu",
            hashed_password=hash_password("adminpass"),
            full_name="Test Admin",
            role="admin",
        ))
        # Warden user
        db.add(User(
            username="test_warden",
            email="test_warden@test.edu",
            hashed_password=hash_password("wardenpass"),
            full_name="Test Warden",
            role="warden",
        ))
        # Resident user (should be denied)
        db.add(User(
            username="test_resident",
            email="test_resident@test.edu",
            hashed_password=hash_password("residentpass"),
            full_name="Test Resident",
            role="student",
        ))
        # Pre-existing active reward
        db.add(RewardCatalogItem(
            name="Existing Canteen Meal",
            description="A pre-existing test reward",
            token_cost=10,
            category="Canteen",
            provider_location="Main Canteen",
            is_active=True,
        ))
        # Pre-existing inactive reward
        db.add(RewardCatalogItem(
            name="Old Laundry Coupon",
            description="An inactive laundry reward",
            token_cost=8,
            category="Laundry",
            provider_location="Ground Floor",
            is_active=False,
        ))
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def get_token(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# AC1 – Admin can list all rewards (active + inactive)
# ─────────────────────────────────────────────────────────────────────────────
class TestAdminListRewards:
    def test_admin_can_list_all_rewards(self, client):
        """AC1: Existing rewards (active and inactive) are returned for admin."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        assert resp.status_code == 200
        rewards = resp.json()
        assert isinstance(rewards, list)
        assert len(rewards) >= 2  # seeded active + inactive rewards
        names = [r["name"] for r in rewards]
        assert "Existing Canteen Meal" in names
        assert "Old Laundry Coupon" in names  # inactive still listed

    def test_admin_list_includes_inactive(self, client):
        """AC1: Admin list includes inactive rewards that residents cannot see."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        rewards = resp.json()
        has_inactive = any(not r["is_active"] for r in rewards)
        assert has_inactive, "Admin list should include inactive rewards"

    def test_warden_can_list_rewards(self, client):
        """AC1: Warden also has access to list all rewards."""
        token = get_token(client, "test_warden", "wardenpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_response_includes_admin_fields(self, client):
        """AC1: Response includes created_at and updated_at for admin management."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        rewards = resp.json()
        assert len(rewards) > 0
        reward = rewards[0]
        assert "created_at" in reward
        assert "updated_at" in reward
        assert "is_active" in reward


# ─────────────────────────────────────────────────────────────────────────────
# AC2 – Admin can create a reward
# ─────────────────────────────────────────────────────────────────────────────
class TestAdminCreateReward:
    def test_admin_creates_reward_successfully(self, client):
        """AC2: Admin submits valid details and reward is added to catalog."""
        token = get_token(client, "test_admin", "adminpass")
        payload = {
            "name": "Free Laundry Wash",
            "description": "One free wash cycle at any hostel laundry",
            "token_cost": 15,
            "category": "Laundry",
            "provider_location": "Ground Floor Laundry",
        }
        resp = client.post("/api/admin/rewards", json=payload, headers=auth_headers(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Free Laundry Wash"
        assert data["token_cost"] == 15
        assert data["category"] == "Laundry"
        assert data["is_active"] is True  # newly created rewards are active by default
        assert "id" in data

    def test_warden_creates_reward_successfully(self, client):
        """AC2: Warden can also create a reward."""
        token = get_token(client, "test_warden", "wardenpass")
        payload = {
            "name": "Hostel Store Discount",
            "description": "10% off at the hostel store",
            "token_cost": 20,
            "category": "Hostel Stores",
            "provider_location": "Hostel Block B",
        }
        resp = client.post("/api/admin/rewards", json=payload, headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "Hostel Store Discount"

    def test_create_reward_with_zero_token_cost_fails(self, client):
        """AC2: Validation rejects token_cost <= 0."""
        token = get_token(client, "test_admin", "adminpass")
        payload = {
            "name": "Invalid Reward",
            "description": "Should fail",
            "token_cost": 0,
            "category": "Canteen",
        }
        resp = client.post("/api/admin/rewards", json=payload, headers=auth_headers(token))
        assert resp.status_code == 422  # Pydantic validation error

    def test_created_reward_appears_in_catalog(self, client):
        """AC2: Newly created reward appears in the admin list."""
        token = get_token(client, "test_admin", "adminpass")
        # Create
        payload = {
            "name": "Special Canteen Snack",
            "description": "A snack from the canteen",
            "token_cost": 5,
            "category": "Canteen",
        }
        create_resp = client.post("/api/admin/rewards", json=payload, headers=auth_headers(token))
        assert create_resp.status_code == 201

        # Verify in list
        list_resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        names = [r["name"] for r in list_resp.json()]
        assert "Special Canteen Snack" in names


# ─────────────────────────────────────────────────────────────────────────────
# AC3 – Admin can update token cost and availability
# ─────────────────────────────────────────────────────────────────────────────
class TestAdminUpdateReward:
    @pytest.fixture
    def created_reward_id(self, client):
        """Create a reward and return its id for update tests."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.post("/api/admin/rewards", json={
            "name": "Updatable Reward",
            "description": "Will be updated in tests",
            "token_cost": 10,
            "category": "Canteen",
        }, headers=auth_headers(token))
        return resp.json()["id"], token

    def test_admin_updates_token_cost(self, client, created_reward_id):
        """AC3: Admin changes token cost and updated value appears in catalog."""
        reward_id, token = created_reward_id
        resp = client.put(
            f"/api/admin/rewards/{reward_id}",
            json={"token_cost": 99},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["token_cost"] == 99

    def test_admin_deactivates_reward(self, client, created_reward_id):
        """AC3: Admin sets is_active=False and reward shows as inactive."""
        reward_id, token = created_reward_id
        resp = client.put(
            f"/api/admin/rewards/{reward_id}",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_admin_reactivates_reward(self, client, created_reward_id):
        """AC3: Admin sets is_active=True and reward returns to active status."""
        reward_id, token = created_reward_id
        # Deactivate first
        client.put(f"/api/admin/rewards/{reward_id}", json={"is_active": False}, headers=auth_headers(token))
        # Reactivate
        resp = client.put(
            f"/api/admin/rewards/{reward_id}",
            json={"is_active": True},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_admin_updates_description(self, client, created_reward_id):
        """AC3: Admin changes description and updated value appears in response."""
        reward_id, token = created_reward_id
        resp = client.put(
            f"/api/admin/rewards/{reward_id}",
            json={"description": "Updated description"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    def test_update_nonexistent_reward_returns_404(self, client):
        """AC3: Updating a reward that doesn't exist returns 404."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.put("/api/admin/rewards/99999", json={"token_cost": 50}, headers=auth_headers(token))
        assert resp.status_code == 404

    def test_soft_delete_hides_from_resident_catalog(self, client, created_reward_id):
        """AC3: After deactivation, the reward no longer appears in the public catalog."""
        reward_id, token = created_reward_id
        # Deactivate via admin
        client.put(f"/api/admin/rewards/{reward_id}", json={"is_active": False}, headers=auth_headers(token))
        # Resident sees only active rewards via public endpoint
        resident_token = get_token(client, "test_resident", "residentpass")
        resp = client.get("/api/rewards", headers=auth_headers(resident_token))
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert reward_id not in ids


# ─────────────────────────────────────────────────────────────────────────────
# AC4 – Unauthorized access denied
# ─────────────────────────────────────────────────────────────────────────────
class TestUnauthorizedAccess:
    def test_resident_cannot_list_admin_rewards(self, client):
        """AC4: Resident receives 403 on GET /api/admin/rewards."""
        token = get_token(client, "test_resident", "residentpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_resident_cannot_create_reward(self, client):
        """AC4: Resident receives 403 on POST /api/admin/rewards."""
        token = get_token(client, "test_resident", "residentpass")
        resp = client.post("/api/admin/rewards", json={
            "name": "Fake Reward",
            "description": "Should be denied",
            "token_cost": 5,
            "category": "Canteen",
        }, headers=auth_headers(token))
        assert resp.status_code == 403

    def test_resident_cannot_update_reward(self, client):
        """AC4: Resident receives 403 on PUT /api/admin/rewards/{id}."""
        # Get any real reward id
        admin_token = get_token(client, "test_admin", "adminpass")
        list_resp = client.get("/api/admin/rewards", headers=auth_headers(admin_token))
        reward_id = list_resp.json()[0]["id"]

        token = get_token(client, "test_resident", "residentpass")
        resp = client.put(f"/api/admin/rewards/{reward_id}", json={"token_cost": 1}, headers=auth_headers(token))
        assert resp.status_code == 403

    def test_resident_cannot_delete_reward(self, client):
        """AC4: Resident receives 403 on DELETE /api/admin/rewards/{id}."""
        admin_token = get_token(client, "test_admin", "adminpass")
        list_resp = client.get("/api/admin/rewards", headers=auth_headers(admin_token))
        reward_id = list_resp.json()[0]["id"]

        token = get_token(client, "test_resident", "residentpass")
        resp = client.delete(f"/api/admin/rewards/{reward_id}", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_unauthenticated_request_denied(self, client):
        """AC4: Unauthenticated request (no token) to admin endpoints returns 403."""
        resp = client.get("/api/admin/rewards")
        assert resp.status_code in (401, 403)

    def test_deny_error_message_is_descriptive(self, client):
        """AC4: Denial response contains a clear 'access denied' message."""
        token = get_token(client, "test_resident", "residentpass")
        resp = client.get("/api/admin/rewards", headers=auth_headers(token))
        assert resp.status_code == 403
        detail = resp.json().get("detail", "").lower()
        assert "access denied" in detail or "only admin" in detail


# ─────────────────────────────────────────────────────────────────────────────
# Soft-delete endpoint (DELETE)
# ─────────────────────────────────────────────────────────────────────────────
class TestSoftDelete:
    def test_admin_soft_deletes_reward(self, client):
        """DELETE endpoint deactivates (soft-deletes) a reward."""
        token = get_token(client, "test_admin", "adminpass")
        # Create a reward to delete
        create_resp = client.post("/api/admin/rewards", json={
            "name": "To Be Deleted",
            "description": "This will be soft-deleted",
            "token_cost": 3,
            "category": "Canteen",
        }, headers=auth_headers(token))
        reward_id = create_resp.json()["id"]

        # Soft-delete it
        del_resp = client.delete(f"/api/admin/rewards/{reward_id}", headers=auth_headers(token))
        assert del_resp.status_code == 200
        assert del_resp.json()["is_active"] is False

    def test_soft_delete_nonexistent_returns_404(self, client):
        """DELETE on non-existent reward returns 404."""
        token = get_token(client, "test_admin", "adminpass")
        resp = client.delete("/api/admin/rewards/99999", headers=auth_headers(token))
        assert resp.status_code == 404
