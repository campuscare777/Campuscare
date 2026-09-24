from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.services.lost_and_found_service import LostAndFoundService
from app.schemas.lost_and_found import (
    LostAndFoundCreate,
    LostAndFoundUpdate,
    LostAndFoundStatusUpdate,
    LostAndFoundResponse,
    LostAndFoundListResponse,
    LostAndFoundStatusHistoryResponse,
)

router = APIRouter(prefix="/api/lost-and-found", tags=["lost-and-found"])


@router.post("", response_model=LostAndFoundResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=LostAndFoundResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_lost_and_found_report(
    payload: LostAndFoundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new lost or found item report (AC1)."""
    service = LostAndFoundService(db)
    report = service.create_report(reporter_id=current_user.id, payload=payload)
    return LostAndFoundResponse.model_validate(report)


@router.get("", response_model=LostAndFoundListResponse)
@router.get("/", response_model=LostAndFoundListResponse, include_in_schema=False)
def list_lost_and_found_reports(
    report_type: Optional[str] = Query(None),
    item_category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    reporter_id: Optional[int] = Query(None),
    hostel_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List lost and found item reports with optional filters."""
    service = LostAndFoundService(db)
    reports = service.list_reports(
        report_type=report_type,
        item_category=item_category,
        status=status,
        reporter_id=reporter_id,
        hostel_type=hostel_type,
    )
    return LostAndFoundListResponse(
        reports=[LostAndFoundResponse.model_validate(r) for r in reports],
        total=len(reports),
    )


@router.get("/{item_report_id}", response_model=LostAndFoundResponse)
def get_lost_and_found_report(
    item_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single lost and found item report by ID (AC1)."""
    service = LostAndFoundService(db)
    report = service.get_report(item_report_id)
    return LostAndFoundResponse.model_validate(report)


@router.patch("/{item_report_id}/status", response_model=LostAndFoundResponse)
def update_lost_and_found_status(
    item_report_id: int,
    payload: LostAndFoundStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update item status (staff/admin action) (AC2, AC3)."""
    service = LostAndFoundService(db)
    report = service.update_status(
        item_report_id=item_report_id,
        changed_by_id=current_user.id,
        payload=payload,
    )
    return LostAndFoundResponse.model_validate(report)


@router.put("/{item_report_id}", response_model=LostAndFoundResponse)
def update_lost_and_found_report(
    item_report_id: int,
    payload: LostAndFoundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update details of a lost and found report."""
    service = LostAndFoundService(db)
    report = service.update_report(item_report_id=item_report_id, payload=payload)
    return LostAndFoundResponse.model_validate(report)


@router.get("/{item_report_id}/history", response_model=List[LostAndFoundStatusHistoryResponse])
def get_lost_and_found_history(
    item_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status transition audit history for a lost and found report."""
    service = LostAndFoundService(db)
    history = service.get_status_history(item_report_id)
    return [LostAndFoundStatusHistoryResponse.model_validate(h) for h in history]
