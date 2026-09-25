from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime

from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.services.lost_and_found_service import LostAndFoundService, STAFF_ROLES
from app.schemas.lost_and_found import (
    LostAndFoundCreate,
    LostAndFoundUpdate,
    LostAndFoundStatusUpdate,
    LostAndFoundClaimRequest,
    LostAndFoundClaimReview,
    LostAndFoundClaimHandover,
    LostAndFoundClaimResponse,
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
    hide_closed: bool = Query(False, description="Hide closed/returned items (AC4)"),
    my_reports: bool = Query(False, description="Filter to current user's reports only"),
    search: Optional[str] = Query(None, description="Search query keyword across items"),
    date_from: Optional[datetime] = Query(None, description="Filter items reported on or after this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter items reported on or before this date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List lost and found item reports with optional filters.
    
    - AC1: Displays active item reports on page load
    - AC2: Filter by category, hostel type, report type, date range, or search keywords
    - AC4: Use hide_closed=true to exclude Closed/Returned items from active listings
    """
    service = LostAndFoundService(db)
    
    target_reporter_id = reporter_id
    if my_reports:
        target_reporter_id = current_user.id

    reports = service.list_reports(
        report_type=report_type,
        item_category=item_category,
        status=status,
        reporter_id=target_reporter_id,
        hostel_type=hostel_type,
        hide_closed=hide_closed,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    
    return LostAndFoundListResponse(
        reports=[LostAndFoundResponse.model_validate(r) for r in reports],
        total=len(reports),
    )


@router.post("/{item_report_id}/claim", response_model=LostAndFoundResponse)
def claim_lost_and_found_report(
    item_report_id: int,
    payload: Optional[LostAndFoundClaimRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a claim request on a lost/found item report (AC1, AC2).
    
    Creates a claim request record and transitions item status to 'Claim Requested'
    for authorized staff verification.
    """
    service = LostAndFoundService(db)
    report = service.claim_report(
        item_report_id=item_report_id,
        claimant_id=current_user.id,
        claim_notes=payload.claim_notes if payload else None,
        proof_details=payload.proof_details if payload else None,
        identifying_info=payload.identifying_info if payload else None,
        contact_number=payload.contact_number if payload else None,
    )
    return LostAndFoundResponse.model_validate(report)


@router.get("/claims", response_model=List[LostAndFoundClaimResponse])
def list_claims(
    item_report_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    my_claims: bool = Query(False, description="Filter to current resident's claims only"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List item claims.
    - Authorized staff can view all submitted claims or filter by item and status.
    - Residents view their own claims with status and rejection reasons (AC4).
    """
    service = LostAndFoundService(db)
    claimant_id = None
    if my_claims or current_user.role not in STAFF_ROLES:
        claimant_id = current_user.id

    claims = service.list_claims(
        item_report_id=item_report_id,
        claimant_id=claimant_id,
        status=status,
    )
    return [LostAndFoundClaimResponse.model_validate(c) for c in claims]


@router.get("/claims/{claim_id}", response_model=LostAndFoundClaimResponse)
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a specific claim."""
    service = LostAndFoundService(db)
    claim = service.get_claim(claim_id)
    if current_user.role not in STAFF_ROLES and claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own claims")
    return LostAndFoundClaimResponse.model_validate(claim)


@router.post("/claims/{claim_id}/verify", response_model=LostAndFoundClaimResponse)
def verify_claim(
    claim_id: int,
    payload: Optional[LostAndFoundClaimReview] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AC3: Authorized staff approves claim.
    Changes claim status to 'Verified' and item report status to 'Verified'.
    """
    service = LostAndFoundService(db)
    claim = service.review_claim(
        claim_id=claim_id,
        staff_user=current_user,
        action="approve",
        notes=payload.notes if payload else None,
    )
    return LostAndFoundClaimResponse.model_validate(claim)


@router.post("/claims/{claim_id}/reject", response_model=LostAndFoundClaimResponse)
def reject_claim(
    claim_id: int,
    payload: LostAndFoundClaimReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AC4: Authorized staff rejects claim with reason.
    Stores the rejection reason and displays it to claimant.
    """
    service = LostAndFoundService(db)
    claim = service.review_claim(
        claim_id=claim_id,
        staff_user=current_user,
        action="reject",
        rejection_reason=payload.rejection_reason,
        notes=payload.notes,
    )
    return LostAndFoundClaimResponse.model_validate(claim)


@router.post("/claims/{claim_id}/handover", response_model=LostAndFoundClaimResponse)
def confirm_item_handover(
    claim_id: int,
    payload: Optional[LostAndFoundClaimHandover] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AC5: Staff confirms item handover to claimant.
    Changes item report status to 'Returned' and closure timestamp is saved.
    """
    service = LostAndFoundService(db)
    claim = service.confirm_handover(
        claim_id=claim_id,
        staff_user=current_user,
        handover_notes=payload.handover_notes if payload else None,
    )
    return LostAndFoundClaimResponse.model_validate(claim)


@router.get("/{item_report_id}/claims", response_model=List[LostAndFoundClaimResponse])
def get_claims_for_item_report(
    item_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve claims associated with a specific item report."""
    service = LostAndFoundService(db)
    claimant_id = None
    if current_user.role not in STAFF_ROLES:
        claimant_id = current_user.id
    claims = service.list_claims(item_report_id=item_report_id, claimant_id=claimant_id)
    return [LostAndFoundClaimResponse.model_validate(c) for c in claims]


@router.get("/{item_report_id}", response_model=LostAndFoundResponse)
def get_lost_and_found_report(
    item_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single lost and found item report by ID (AC3).

    Access permissions (AC3):
    - Staff/Admin: full access to all reports.
    - Residents: can view their own reports at any status, AND any report
      whose status is in the publicly visible set (Published, Claim Requested,
      Verified, Returned, Closed, Received by Staff).
    - Submitted / Under Review items from OTHER reporters are private until
      staff publish them.
    """
    service = LostAndFoundService(db)
    report = service.get_report(item_report_id)

    # AC3: Access permission enforcement
    STAFF_ROLES_LOCAL = ["admin", "warden", "staff", "hostel_staff"]
    PUBLIC_STATUSES = {
        "Published", "Claim Requested", "Verified",
        "Returned", "Closed", "Received by Staff",
    }
    is_staff = current_user.role in STAFF_ROLES_LOCAL
    is_own_report = report.reporter_id == current_user.id
    is_public_status = report.status in PUBLIC_STATUSES

    if not is_staff and not is_own_report and not is_public_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report is not yet publicly visible. Only the reporter or staff can view it.",
        )

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