from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.user import LoginRequest, TokenPair, UserResponse, UserCreate
from app.services.auth_service import verify_password, create_access_token, get_current_user, require_roles, hash_password
from app.repositories.user_repository import UserRepository
from app.models.user import User, ROLE_ADMIN, ALL_ROLES

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenPair(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Admin: User Management (HOSTELCARE-CROSS-001)
# ---------------------------------------------------------------------------

@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: list all registered users with their roles."""
    user_repo = UserRepository(db)
    return [UserResponse.model_validate(u) for u in user_repo.get_all()]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: create a new user with any role."""
    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Allowed: {sorted(ALL_ROLES)}",
        )
    user_repo = UserRepository(db)
    if user_repo.get_by_username(payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if user_repo.get_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        hostel_type=payload.hostel_type,
    )
    return UserResponse.model_validate(user_repo.create(new_user))


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: deactivate a user account (AC4 — deny access)."""
    user_repo = UserRepository(db)
    target = user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
    target.is_active = False
    return UserResponse.model_validate(user_repo.update(target))


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Admin only: reactivate a previously deactivated user account."""
    user_repo = UserRepository(db)
    target = user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    target.is_active = True
    return UserResponse.model_validate(user_repo.update(target))
