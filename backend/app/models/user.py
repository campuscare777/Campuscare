from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean
from app.db.session import Base

# ---------------------------------------------------------------------------
# Role constants — single source of truth for the entire application
# ---------------------------------------------------------------------------
ROLE_STUDENT = "student"                    # Resident
ROLE_WARDEN = "warden"                      # Warden
ROLE_MAINTENANCE = "maintenance"            # Maintenance Staff
ROLE_FOOD_STAFF = "food_staff"              # Food / Mess Staff
ROLE_CANTEEN_STAFF = "canteen_staff"        # Canteen Staff
ROLE_LAUNDRY_STAFF = "laundry_staff"        # Laundry Staff
ROLE_HOSTEL_STORE_STAFF = "hostel_store_staff"  # Hostel Store Staff
ROLE_ADMIN = "admin"                        # System Administrator

ALL_ROLES = {
    ROLE_STUDENT,
    ROLE_WARDEN,
    ROLE_MAINTENANCE,
    ROLE_FOOD_STAFF,
    ROLE_CANTEEN_STAFF,
    ROLE_LAUNDRY_STAFF,
    ROLE_HOSTEL_STORE_STAFF,
    ROLE_ADMIN,
}

# Staff who can manage complaints / lost-and-found items
COMPLAINT_STAFF_ROLES = {ROLE_WARDEN, ROLE_MAINTENANCE, ROLE_FOOD_STAFF, ROLE_ADMIN}

# Staff who can process reward-redemption vouchers
REDEMPTION_STAFF_ROLES = {
    ROLE_CANTEEN_STAFF,
    ROLE_LAUNDRY_STAFF,
    ROLE_HOSTEL_STORE_STAFF,
    ROLE_FOOD_STAFF,
    ROLE_MAINTENANCE,
    ROLE_WARDEN,
    ROLE_ADMIN,
}

# Staff who can manage the reward catalog (create / update / delete rewards)
REWARD_ADMIN_ROLES = {ROLE_WARDEN, ROLE_ADMIN}

# Mapping: staff role → reward category they are authorised to fulfil.
# None means the role can fulfil ALL categories.
ROLE_REDEMPTION_CATEGORY: dict[str, str | None] = {
    ROLE_CANTEEN_STAFF: "Canteen",
    ROLE_LAUNDRY_STAFF: "Laundry",
    ROLE_HOSTEL_STORE_STAFF: "Hostel Stores",
    ROLE_FOOD_STAFF: None,
    ROLE_MAINTENANCE: None,
    ROLE_WARDEN: None,
    ROLE_ADMIN: None,
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30), default="student")
    # Optional: scope warden/canteen/laundry/hostel_store staff to a specific hostel
    hostel_type: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
