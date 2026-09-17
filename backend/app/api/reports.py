from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import os
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.report_service import ReportService
from app.schemas.report import ReportResponse, ReportListResponse, StatusUpdateRequest, StatusHistoryResponse, VerifyRequest
from app.models.user import User
from app.core.locations import CAMPUS_LOCATIONS

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/locations")
def get_locations():
    """Return pre-defined campus locations list."""
    return CAMPUS_LOCATIONS


@router.post("", response_model=ReportResponse)
def create_report(
    location: str = Form(...),
    building: Optional[str] = Form(None),
    floor: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not location or not location.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both a photo and a location are required to submit a report"
        )
    if not photo or not photo.filename or not photo.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both a photo and a location are required to submit a report"
        )

    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, photo.filename)
    with open(file_path, "wb") as f:
        f.write(photo.file.read())

    rel_photo_path = f"uploads/{photo.filename}"

    service = ReportService(db)
    report = service.create_report(
        reporter_id=current_user.id,
        photo_path=rel_photo_path,
        location=location.strip(),
        building=building,
        floor=floor,
        area=area,
        description=description,
    )
    return ReportResponse.model_validate(report)


@router.get("", response_model=ReportListResponse)
def list_reports(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    if current_user.role == "student":
        reports = service.list_reports(reporter_id=current_user.id)
    else:
        reports = service.list_reports(status_filter=status)
    return ReportListResponse(reports=[ReportResponse.model_validate(r) for r in reports], total=len(reports))


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ReportService(db)
    report = service.get_report(report_id)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/verify", response_model=ReportResponse)
def verify_report(
    report_id: int,
    request: Optional[VerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["maintenance", "admin"]:
        raise HTTPException(status_code=403, detail="Only maintenance staff can verify reports")
    reason = request.reason if request else None
    service = ReportService(db)
    report = service.verify_report(report_id, current_user.id, reason)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_status(
    report_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["maintenance", "admin"]:
        raise HTTPException(status_code=403, detail="Only maintenance team can update status")
    service = ReportService(db)
    report = service.update_status(report_id, request.status, current_user.id, request.reason)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/history", response_model=list[StatusHistoryResponse])
def get_history(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ReportService(db)
    history = service.get_status_history(report_id)
    return [StatusHistoryResponse.model_validate(h) for h in history]
