from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import os
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.report_service import ReportService, STAFF_ROLES
from app.schemas.report import (
    ReportResponse, ReportListResponse, StatusUpdateRequest,
    StatusHistoryResponse, VerifyRequest, RejectRequest, AssignRequest
)
from app.models.user import User
from app.core.locations import HOSTEL_TYPES, HOSTEL_LOCATIONS, COMPLAINT_CATEGORIES

router = APIRouter(prefix="/api/reports", tags=["complaints"])


@router.get("/hostel-config")
def get_hostel_config():
    """Return hostel types, per-hostel location structure, and complaint categories for frontend dropdowns."""
    return {
        "hostel_types": HOSTEL_TYPES,
        "hostel_locations": HOSTEL_LOCATIONS,
        "complaint_categories": COMPLAINT_CATEGORIES,
    }


# Backward-compat alias
@router.get("/locations")
def get_locations():
    """Return hostel types as a flat list (backward compat)."""
    return [
        {"id": h.lower().replace(" ", "_"), "name": h, "building": h, "zone": "Residential Zone"}
        for h in HOSTEL_TYPES
    ]


@router.post("", response_model=ReportResponse)
def create_report(
    hostel_type: str = Form(...),
    location: str = Form(...),
    category: str = Form(...),
    building: Optional[str] = Form(None),
    floor: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a hostel complaint. Photo is optional; hostel_type, location, and category are required."""
    photo_path = None
    if photo and photo.filename and photo.filename.strip():
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, photo.filename)
        with open(file_path, "wb") as f:
            f.write(photo.file.read())
        photo_path = f"uploads/{photo.filename}"

    service = ReportService(db)
    report = service.create_report(
        reporter_id=current_user.id,
        hostel_type=hostel_type.strip(),
        location=location.strip(),
        category=category.strip(),
        building=building,
        floor=floor,
        area=area,
        description=description,
        photo_path=photo_path,
    )
    return ReportResponse.model_validate(report)


@router.get("", response_model=ReportListResponse)
def list_reports(
    status: Optional[str] = Query(None),
    hostel_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    food_related: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    if current_user.role == "student":
        # Residents see only their own complaints
        reports = service.list_reports(reporter_id=current_user.id)
    elif current_user.role == "food_staff":
        # Food staff sees ONLY food-related complaints
        reports = service.list_reports(
            status_filter=status,
            hostel_type=hostel_type,
            category=category,
            food_related=True,
        )
    elif current_user.role == "warden":
        # Warden sees ONLY non-food complaints
        reports = service.list_reports(
            status_filter=status,
            hostel_type=hostel_type,
            category=category,
            food_related=False,
        )
    else:
        # Admin & maintenance see all complaints
        reports = service.list_reports(
            status_filter=status,
            hostel_type=hostel_type,
            category=category,
            food_related=food_related,
        )
    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=len(reports)
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ReportService(db)
    report = service.get_report(report_id)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/forward-to-admin", response_model=ReportResponse)
def forward_to_admin(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Food Staff or Warden verifies and forwards the complaint to Admin."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can verify complaints")
    reason = request.reason if request else None
    service = ReportService(db)
    report = service.forward_to_admin(report_id, current_user.id, current_user.role, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/admin-verify", response_model=ReportResponse)
def admin_verify(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin verifies the complaint and Green Tokens are awarded to the student."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can perform Admin Verification and token generation")
    reason = request.reason if request else None
    service = ReportService(db)
    report = service.admin_verify(report_id, current_user.id, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/complete-work", response_model=ReportResponse)
def complete_work(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Staff (Food Staff or Warden) completes the work and reports to Admin."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can complete work on complaints")
    reason = request.reason if request else None
    service = ReportService(db)
    report = service.complete_work(report_id, current_user.id, current_user.role, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/admin-resolve", response_model=ReportResponse)
def admin_resolve(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin confirms final completion and closes the complaint."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can confirm final closure")
    reason = request.reason if request else None
    service = ReportService(db)
    report = service.admin_resolve(report_id, current_user.id, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/verify", response_model=ReportResponse)
def verify_report(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Backward-compatible verify endpoint."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can verify complaints")
    reason = request.reason if request else None
    service = ReportService(db)
    if current_user.role == "admin":
        report = service.admin_verify(report_id, current_user.id, reason)
    else:
        report = service.forward_to_admin(report_id, current_user.id, current_user.role, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/reject", response_model=ReportResponse)
def reject_report(
    report_id: int,
    request: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a complaint with a mandatory reason (staff only)."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can reject complaints")
    service = ReportService(db)
    report = service.reject_report(report_id, current_user.id, request.reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/assign", response_model=ReportResponse)
def assign_report(
    report_id: int,
    request: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a verified complaint to a responsible team (staff only)."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can assign complaints")
    service = ReportService(db)
    report = service.assign_report(report_id, current_user.id, request.assigned_team)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_status(
    report_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only authorised staff can update complaint status")
    if not request.status or not str(request.status).strip():
        raise HTTPException(status_code=400, detail="status field is required")
    service = ReportService(db)
    report = service.update_status(report_id, request.status.strip(), current_user.id, request.reason)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/history", response_model=list[StatusHistoryResponse])
def get_history(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ReportService(db)
    history = service.get_status_history(report_id)
    return [StatusHistoryResponse.model_validate(h) for h in history]
