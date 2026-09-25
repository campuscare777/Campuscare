from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.user import ALL_ROLES


class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str = "student"
    hostel_type: Optional[str] = None


class UserCreate(UserBase):
    password: str

    def validate_role(self) -> "UserCreate":
        if self.role not in ALL_ROLES:
            raise ValueError(f"Invalid role '{self.role}'. Allowed: {sorted(ALL_ROLES)}")
        return self


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str
