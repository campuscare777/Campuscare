from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.report_service import ReportService
from app.schemas.report import ReportResponse, ReportListResponse, StatusUpdateRequest, StatusHistoryResponse
from app.models.user import User

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
def create_report(
    location: str = Form(...),
    building: Optional[str] = Form(None),
    floor: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import os
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, photo.filename)
    with open(file_path, "wb") as f:
        f.write(photo.file.read())

    service = ReportService(db)
    report = service.create_report(
        reporter_id=current_user.id,
        photo_path=file_path,
        location=location,
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


@router.patch("/{report_id}/status", response_model=ReportResponse)
def update_status(
    report_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["maintenance", "admin"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only maintenance team can update status")
    service = ReportService(db)
    report = service.update_status(report_id, request.status, current_user.id, request.reason)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/history", response_model=list[StatusHistoryResponse])
def get_history(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ReportService(db)
    history = service.get_status_history(report_id)
    return [StatusHistoryResponse.model_validate(h) for h in history]
