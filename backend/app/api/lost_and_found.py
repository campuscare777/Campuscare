from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional, List
import os

from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.services.lost_and_found_service import LostAndFoundService, STAFF_ROLES
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
async def create_lost_and_found_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new lost or found item report (AC1, AC2).
    
    - Accepts JSON payload or multipart/form-data image upload (AC3)
    - Generates unique item_report_id as reference ID
    - Validates all required fields
    """
    content_type = request.headers.get("content-type", "")
    image_path = None

    if "application/json" in content_type:
        body = await request.json()
        report_type = body.get("report_type")
        item_category = body.get("item_category")
        item_name = body.get("item_name")
        location = body.get("location")
        description = body.get("description")
        hostel_type = body.get("hostel_type")
        date_lost_or_found = body.get("date_lost_or_found")
        identifying_details = body.get("identifying_details")
        image_path = body.get("image_reference")
    else:
        form = await request.form()
        report_type = form.get("report_type")
        item_category = form.get("item_category")
        item_name = form.get("item_name")
        location = form.get("location")
        description = form.get("description")
        hostel_type = form.get("hostel_type")
        date_lost_or_found = form.get("date_lost_or_found")
        identifying_details = form.get("identifying_details")
        image = form.get("image")
        if image and hasattr(image, "filename") and image.filename and image.filename.strip():
            upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "lost-and-found")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, image.filename)
            content = await image.read()
            with open(file_path, "wb") as f:
                f.write(content)
            image_path = f"uploads/lost-and-found/{image.filename}"

    # Validate required fields
    missing = []
    if not report_type:
        missing.append("report_type")
    if not item_category:
        missing.append("item_category")
    if not item_name:
        missing.append("item_name")
    if not location:
        missing.append("location")
    if missing:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", f], "msg": "Field required", "type": "missing"} for f in missing]
        )

    # Parse date if provided
    from datetime import datetime
    date_lost_or_found_dt = None
    if date_lost_or_found:
        try:
            date_lost_or_found_dt = datetime.fromisoformat(str(date_lost_or_found))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    # Create payload
    payload = LostAndFoundCreate(
        report_type=str(report_type).strip(),
        item_category=str(item_category).strip(),
        item_name=str(item_name).strip(),
        location=str(location).strip(),
        description=str(description).strip() if description else None,
        hostel_type=str(hostel_type).strip() if hostel_type else None,
        date_lost_or_found=date_lost_or_found_dt,
        identifying_details=str(identifying_details).strip() if identifying_details else None,
        image_reference=image_path,
    )

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
    hide_closed: bool = Query(False, description="Hide closed/returned items (AC5)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List lost and found item reports with optional filters.
    
    - AC5: Use hide_closed=true to exclude Closed/Returned items
    - Students see only their own reports
    - Staff/Admin see all reports
    """
    service = LostAndFoundService(db)
    
    # Apply role-based filtering
    if current_user.role == "student":
        # Students see only their own reports
        reports = service.list_reports(
            report_type=report_type,
            item_category=item_category,
            status=status,
            reporter_id=current_user.id,
            hostel_type=hostel_type,
            hide_closed=hide_closed,
        )
    else:
        # Staff/Admin see all reports
        reports = service.list_reports(
            report_type=report_type,
            item_category=item_category,
            status=status,
            reporter_id=reporter_id,
            hostel_type=hostel_type,
            hide_closed=hide_closed,
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
    """
    Retrieve a single lost and found item report by ID (AC1).
    
    - AC1: Returns item with unique reference ID (item_report_id)
    - AC4: Includes image_reference if photo was uploaded
    """
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
    """
    Update item status (staff/admin action only) (AC2, AC3).
    
    - AC2: Only staff/admin can update status (role-based authorization)
    - AC3: Saves closure timestamp when status = Returned or Closed
    - AC2: Validates status transitions and assigned staff
    """
    # AC2: Staff-only authorization check
    STAFF_ROLES = ["admin", "warden", "staff", "hostel_staff"]
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff/admin can update lost and found item status"
        )
    
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
    """Update details of a lost and found report (reporter only)."""
    service = LostAndFoundService(db)
    
    # Allow only reporter or admin to edit
    report = service.get_report(item_report_id)
    if current_user.id != report.reporter_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own reports"
        )
    
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