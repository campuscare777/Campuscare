"""
HOSTELCARE-CROSS-001: Authentication and Role-Based Access
==========================================================

Tests covering all 4 acceptance criteria:

AC1: Resident (student role) → can access resident features after login
AC2: Maintenance staff → can access complaint-management features only
AC3: Canteen / Laundry / Hostel Store staff → can process only their relevant rewards
AC4: Unauthorized user → access denied when attempting restricted action
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.services.auth_service import hash_password, create_access_token
from app.models.user import (
    User,
    ALL_ROLES,
    COMPLAINT_STAFF_ROLES,
    REDEMPTION_STAFF_ROLES,
    REWARD_ADMIN_ROLES,
    ROLE_REDEMPTION_CATEGORY,
    ROLE_STUDENT,
    ROLE_WARDEN,
    ROLE_MAINTENANCE,
    ROLE_FOOD_STAFF,
    ROLE_CANTEEN_STAFF,
    ROLE_LAUNDRY_STAFF,
    ROLE_HOSTEL_STORE_STAFF,
    ROLE_ADMIN,
)
from app.models.reward import RewardCatalogItem


# ---------------------------------------------------------------------------
# Fixtures: per-test in-memory database with StaticPool
# ---------------------------------------------------------------------------

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

    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield db
    fastapi_app.dependency_overrides.clear()
    db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_user(db, username, role, password="password123", hostel_type=None, is_active=True):
    u = User(
        username=username,
        email=f"{username}@test.hostelcare.edu",
        hashed_password=hash_password(password),
        full_name=username.replace("_", " ").title(),
        role=role,
        hostel_type=hostel_type,
        is_active=is_active,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _make_reward(db, name, category, token_cost=5):
    r = RewardCatalogItem(
        name=name,
        description=f"{name} reward",
        token_cost=token_cost,
        category=category,
        provider_location="Campus",
        is_active=True,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _token(user):
    return create_access_token({"sub": str(user.id), "role": user.role})


def _auth(user):
    return {"Authorization": f"Bearer {_token(user)}"}


client = TestClient(fastapi_app)


# ===========================================================================
# Role constants sanity checks
# ===========================================================================

def test_all_roles_defined():
    """All 8 roles specified in CROSS-001 are present in ALL_ROLES."""
    expected = {
        ROLE_STUDENT,
        ROLE_WARDEN,
        ROLE_MAINTENANCE,
        ROLE_FOOD_STAFF,
        ROLE_CANTEEN_STAFF,
        ROLE_LAUNDRY_STAFF,
        ROLE_HOSTEL_STORE_STAFF,
        ROLE_ADMIN,
    }
    assert expected == ALL_ROLES, f"Missing roles: {expected - ALL_ROLES}"


def test_role_sets_are_disjoint_where_expected():
    """Residents should NOT appear in any staff set."""
    assert ROLE_STUDENT not in COMPLAINT_STAFF_ROLES
    assert ROLE_STUDENT not in REDEMPTION_STAFF_ROLES
    assert ROLE_STUDENT not in REWARD_ADMIN_ROLES
    # New redemption-scoped roles should NOT be in complaint staff
    assert ROLE_CANTEEN_STAFF not in COMPLAINT_STAFF_ROLES
    assert ROLE_LAUNDRY_STAFF not in COMPLAINT_STAFF_ROLES
    assert ROLE_HOSTEL_STORE_STAFF not in COMPLAINT_STAFF_ROLES


def test_redemption_category_map_covers_all_scoped_staff():
    """Every role-scoped redemption staff role has a category mapping."""
    scoped = {ROLE_CANTEEN_STAFF, ROLE_LAUNDRY_STAFF, ROLE_HOSTEL_STORE_STAFF}
    for role in scoped:
        assert role in ROLE_REDEMPTION_CATEGORY
        assert ROLE_REDEMPTION_CATEGORY[role] is not None


# ===========================================================================
# Login & JWT
# ===========================================================================

def test_login_returns_jwt_and_user_with_role(test_db):
    """Login endpoint returns JWT + user object including role (all roles work)."""
    _make_user(test_db, "test_resident", ROLE_STUDENT)

    res = client.post("/api/login", json={"username": "test_resident", "password": "password123"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == ROLE_STUDENT
    assert data["user"]["username"] == "test_resident"


def test_login_invalid_credentials_returns_401(test_db):
    res = client.post("/api/login", json={"username": "nobody", "password": "wrong"})
    assert res.status_code == 401


def test_login_inactive_user_returns_403(test_db):
    """Deactivated accounts are rejected at login (AC4)."""
    _make_user(test_db, "inactive_user", ROLE_STUDENT, is_active=False)

    res = client.post("/api/login", json={"username": "inactive_user", "password": "password123"})
    assert res.status_code == 403


def test_me_endpoint_returns_correct_role(test_db):
    """GET /api/me returns the authenticated user with their role."""
    user = _make_user(test_db, "test_warden", ROLE_WARDEN)

    res = client.get("/api/me", headers=_auth(user))
    assert res.status_code == 200
    assert res.json()["role"] == ROLE_WARDEN


# ===========================================================================
# AC1 – Resident features available after login
# ===========================================================================

def test_ac1_resident_can_login_and_see_own_complaints(test_db):
    """AC1: Resident logs in and can access the reports endpoint."""
    resident = _make_user(test_db, "resident_ac1", ROLE_STUDENT)

    res = client.get("/api/reports", headers=_auth(resident))
    assert res.status_code == 200


def test_ac1_resident_can_view_token_balance(test_db):
    """AC1: Resident can check their Green Token balance."""
    resident = _make_user(test_db, "resident_tokens", ROLE_STUDENT)

    res = client.get("/api/tokens/balance", headers=_auth(resident))
    assert res.status_code == 200
    data = res.json()
    assert "balance" in data


def test_ac1_resident_can_view_reward_catalog(test_db):
    """AC1: Resident can browse the full reward catalog."""
    resident = _make_user(test_db, "resident_rewards", ROLE_STUDENT)
    _make_reward(test_db, "Free Canteen Meal", "Canteen")
    _make_reward(test_db, "Laundry Token", "Laundry")

    res = client.get("/api/rewards", headers=_auth(resident))
    assert res.status_code == 200
    categories = {r["category"] for r in res.json()}
    # Residents see ALL categories
    assert "Canteen" in categories
    assert "Laundry" in categories


def test_ac1_unauthenticated_request_denied():
    """AC1 inverse: unauthenticated request to any protected endpoint returns 403."""
    res = client.get("/api/reports")
    assert res.status_code in (401, 403)


# ===========================================================================
# AC2 – Maintenance staff: complaint features, NOT reward admin
# ===========================================================================

def test_ac2_maintenance_can_access_complaints(test_db):
    """AC2: Maintenance staff can access the complaints endpoint."""
    maint = _make_user(test_db, "maint_ac2", ROLE_MAINTENANCE)

    res = client.get("/api/reports", headers=_auth(maint))
    assert res.status_code == 200


def test_ac2_maintenance_in_complaint_staff_roles():
    """AC2: maintenance is included in COMPLAINT_STAFF_ROLES."""
    assert ROLE_MAINTENANCE in COMPLAINT_STAFF_ROLES


def test_ac2_maintenance_cannot_manage_reward_catalog(test_db):
    """AC2: Maintenance staff cannot create or manage rewards (only admin/warden can)."""
    maint = _make_user(test_db, "maint_reward_deny", ROLE_MAINTENANCE)

    res = client.get("/api/admin/rewards", headers=_auth(maint))
    assert res.status_code == 403

    res = client.post("/api/admin/rewards", headers=_auth(maint), json={
        "name": "Test Reward", "description": "Test", "token_cost": 5,
        "category": "Canteen", "provider_location": "Canteen Block"
    })
    assert res.status_code == 403


def test_ac2_food_staff_in_complaint_staff_roles():
    """AC2: food_staff is included in COMPLAINT_STAFF_ROLES."""
    assert ROLE_FOOD_STAFF in COMPLAINT_STAFF_ROLES


def test_ac2_warden_in_complaint_staff_roles():
    """AC2: warden is included in COMPLAINT_STAFF_ROLES."""
    assert ROLE_WARDEN in COMPLAINT_STAFF_ROLES


# ===========================================================================
# AC3 – Canteen / Laundry / Hostel Store staff: scoped redemptions
# ===========================================================================

def test_ac3_canteen_staff_sees_only_canteen_rewards(test_db):
    """AC3: Canteen staff listing rewards sees only Canteen category."""
    canteen = _make_user(test_db, "canteen_ac3", ROLE_CANTEEN_STAFF)
    _make_reward(test_db, "Canteen Meal", "Canteen")
    _make_reward(test_db, "Laundry 1kg", "Laundry")
    _make_reward(test_db, "Store Pen", "Hostel Stores")

    res = client.get("/api/rewards", headers=_auth(canteen))
    assert res.status_code == 200
    categories = {r["category"] for r in res.json()}
    assert categories == {"Canteen"}, f"Expected only Canteen, got {categories}"


def test_ac3_laundry_staff_sees_only_laundry_rewards(test_db):
    """AC3: Laundry staff listing rewards sees only Laundry category."""
    laundry = _make_user(test_db, "laundry_ac3", ROLE_LAUNDRY_STAFF)
    _make_reward(test_db, "Canteen Meal", "Canteen")
    _make_reward(test_db, "Laundry 1kg", "Laundry")

    res = client.get("/api/rewards", headers=_auth(laundry))
    assert res.status_code == 200
    categories = {r["category"] for r in res.json()}
    assert categories == {"Laundry"}, f"Expected only Laundry, got {categories}"


def test_ac3_hostel_store_staff_sees_only_hostel_store_rewards(test_db):
    """AC3: Hostel Store staff sees only Hostel Stores category."""
    store = _make_user(test_db, "store_ac3", ROLE_HOSTEL_STORE_STAFF)
    _make_reward(test_db, "Canteen Meal", "Canteen")
    _make_reward(test_db, "Store Pencil", "Hostel Stores")

    res = client.get("/api/rewards", headers=_auth(store))
    assert res.status_code == 200
    categories = {r["category"] for r in res.json()}
    assert categories == {"Hostel Stores"}, f"Expected only Hostel Stores, got {categories}"


def test_ac3_warden_sees_all_reward_categories(test_db):
    """AC3: Warden sees all reward categories (no scope restriction)."""
    warden = _make_user(test_db, "warden_ac3", ROLE_WARDEN)
    _make_reward(test_db, "Canteen Meal", "Canteen")
    _make_reward(test_db, "Laundry 1kg", "Laundry")
    _make_reward(test_db, "Store Pencil", "Hostel Stores")

    res = client.get("/api/rewards", headers=_auth(warden))
    assert res.status_code == 200
    categories = {r["category"] for r in res.json()}
    assert "Canteen" in categories
    assert "Laundry" in categories
    assert "Hostel Stores" in categories


def test_ac3_resident_cannot_fulfill_redemption_vouchers(test_db):
    """AC3: Residents cannot look up or fulfill redemption vouchers."""
    resident = _make_user(test_db, "resident_redeem_deny", ROLE_STUDENT)

    res = client.get("/api/redemptions/FAKE-VOUCHER-REF", headers=_auth(resident))
    assert res.status_code == 403


def test_ac3_maintenance_can_lookup_redemption_vouchers(test_db):
    """AC3: Maintenance/food staff retain backward-compat access to redemptions."""
    maint = _make_user(test_db, "maint_redeem_ok", ROLE_MAINTENANCE)
    food = _make_user(test_db, "food_redeem_ok", ROLE_FOOD_STAFF)

    # Both can attempt lookup (will get 404 for non-existent voucher, not 403)
    res = client.get("/api/redemptions/FAKE-VOUCHER-REF", headers=_auth(maint))
    assert res.status_code == 404  # not 403
    res = client.get("/api/redemptions/FAKE-VOUCHER-REF", headers=_auth(food))
    assert res.status_code == 404  # not 403


# ===========================================================================
# AC4 – Unauthorized user → access denied
# ===========================================================================

def test_ac4_resident_cannot_access_admin_reward_management(test_db):
    """AC4: Resident cannot create, update, or delete rewards."""
    resident = _make_user(test_db, "resident_admin_deny", ROLE_STUDENT)

    res = client.get("/api/admin/rewards", headers=_auth(resident))
    assert res.status_code == 403


def test_ac4_resident_cannot_list_all_users(test_db):
    """AC4: Resident cannot access the admin user list endpoint."""
    resident = _make_user(test_db, "resident_users_deny", ROLE_STUDENT)

    res = client.get("/api/users", headers=_auth(resident))
    assert res.status_code == 403


def test_ac4_admin_can_list_all_users(test_db):
    """AC4: Admin can list all users."""
    admin = _make_user(test_db, "admin_ac4", ROLE_ADMIN)
    _make_user(test_db, "another_user", ROLE_STUDENT)

    res = client.get("/api/users", headers=_auth(admin))
    assert res.status_code == 200
    usernames = [u["username"] for u in res.json()]
    assert "another_user" in usernames


def test_ac4_admin_can_deactivate_user(test_db):
    """AC4: Admin can deactivate a user, cutting off their access."""
    admin = _make_user(test_db, "admin_deact", ROLE_ADMIN)
    target = _make_user(test_db, "target_user", ROLE_STUDENT)

    res = client.patch(f"/api/users/{target.id}/deactivate", headers=_auth(admin))
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_ac4_deactivated_user_cannot_authenticate(test_db):
    """AC4: A deactivated user's token is rejected at the API level."""
    user = _make_user(test_db, "deact_user", ROLE_STUDENT)
    token = _token(user)  # capture token before deactivation
    user.is_active = False
    test_db.commit()

    # Token was valid but account is now inactive
    res = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_ac4_canteen_staff_cannot_verify_complaints(test_db):
    """AC4: Canteen staff cannot approve/reject hostel complaints."""
    canteen = _make_user(test_db, "canteen_complaint_deny", ROLE_CANTEEN_STAFF)

    res = client.patch("/api/reports/999/verify", headers=_auth(canteen), json={"reason": "test"})
    assert res.status_code == 403


def test_ac4_invalid_token_rejected():
    """AC4: A completely invalid Bearer token is rejected."""
    res = client.get("/api/me", headers={"Authorization": "Bearer totally-invalid-token"})
    assert res.status_code == 401


def test_ac4_admin_create_user_with_valid_role(test_db):
    """AC4: Admin can create a user with any valid role."""
    admin = _make_user(test_db, "admin_create", ROLE_ADMIN)

    res = client.post("/api/users", headers=_auth(admin), json={
        "username": "new_canteen",
        "email": "new_canteen@hostelcare.edu",
        "password": "pass1234",
        "full_name": "New Canteen",
        "role": ROLE_CANTEEN_STAFF,
    })
    assert res.status_code == 201
    assert res.json()["role"] == ROLE_CANTEEN_STAFF


def test_ac4_admin_cannot_create_user_with_invalid_role(test_db):
    """AC4: Admin attempt to create user with unknown role is rejected."""
    admin = _make_user(test_db, "admin_bad_role", ROLE_ADMIN)

    res = client.post("/api/users", headers=_auth(admin), json={
        "username": "bad_role_user",
        "email": "badrole@hostelcare.edu",
        "password": "pass1234",
        "full_name": "Bad Role",
        "role": "super_villain",
    })
    assert res.status_code == 400


def test_ac4_non_admin_cannot_create_users(test_db):
    """AC4: Non-admin (warden) cannot create new user accounts."""
    warden = _make_user(test_db, "warden_create_deny", ROLE_WARDEN)

    res = client.post("/api/users", headers=_auth(warden), json={
        "username": "unauthorized_create",
        "email": "unauth@hostelcare.edu",
        "password": "pass1234",
        "full_name": "Unauth User",
        "role": ROLE_STUDENT,
    })
    assert res.status_code == 403
