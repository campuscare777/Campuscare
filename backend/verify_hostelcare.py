import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal, Base, engine
from app.models.report import Report, ReportStatusHistory
from app.models.reward import RewardCatalogItem
from app.models.token import TokenBalance, TokenTransaction
from app.models.user import User
from app.core.config import get_settings
settings = get_settings()
from app.core.locations import HOSTEL_LOCATIONS, HOSTEL_TYPES, COMPLAINT_CATEGORIES
from app.services.report_service import ReportService
from app.services.reward_service import RewardCatalogService
from app.services.token_service import RewardRedemptionService, TokenAwardService
from app.services.dashboard_service import DashboardService
from app.schemas.report import ReportCreate

def test_hostelcare_backend():
    print("=== 1. Checking Settings & Hostel Config ===")
    print(f"App Name: {settings.APP_NAME}")
    assert "HostelCare" in settings.APP_NAME, "App name should contain HostelCare"
    print(f"Configured Hostel Types: {HOSTEL_TYPES}")
    assert "Boys Hostel" in HOSTEL_TYPES
    assert "Girls Hostel" in HOSTEL_TYPES
    assert "NRI Hostel" in HOSTEL_TYPES
    print(f"Configured Complaint Categories: {COMPLAINT_CATEGORIES}")
    assert "Plumbing" in COMPLAINT_CATEGORIES
    assert "Electrical" in COMPLAINT_CATEGORIES
    assert "Food/Mess" in COMPLAINT_CATEGORIES

    print("\n=== 2. Checking Database Models & Schema ===")
    db = SessionLocal()
    try:
        # Check Report columns
        r_cols = [c.name for c in Report.__table__.columns]
        print(f"Report columns: {r_cols}")
        for field in ["hostel_type", "category", "food_related", "assigned_team", "resolved_at"]:
            assert field in r_cols, f"Missing {field} in Report table"

        # Check RewardCatalogItem columns
        rew_cols = [c.name for c in RewardCatalogItem.__table__.columns]
        print(f"Reward columns: {rew_cols}")
        for field in ["category", "provider_location"]:
            assert field in rew_cols, f"Missing {field} in RewardCatalogItem table"

        # Check TokenTransaction columns
        tok_cols = [c.name for c in TokenTransaction.__table__.columns]
        print(f"TokenTransaction columns: {tok_cols}")
        assert "redemption_reference" in tok_cols, "Missing redemption_reference in TokenTransaction"

        # Check Users in DB
        users = db.query(User).all()
        print(f"Users in DB ({len(users)}): {[u.username + ' (' + u.role + ')' for u in users]}")
        roles = {u.role for u in users}
        assert "warden" in roles, "Warden user should exist"
        assert "food_staff" in roles, "Food staff user should exist"

        # Check Reports in DB
        reports = db.query(Report).all()
        print(f"Complaints in DB ({len(reports)}): {[f'#{r.id} {r.hostel_type} - {r.category} ({r.status})' for r in reports[:4]]}")
        assert len(reports) > 0, "Complaints should exist in DB"

        # Check Rewards in DB
        rewards = db.query(RewardCatalogItem).all()
        print(f"Rewards in DB ({len(rewards)}): {[f'{r.name} [{r.category}] ({r.token_cost} tok)' for r in rewards[:4]]}")
        assert len(rewards) > 0, "Rewards should exist in DB"

        print("\n=== 3. Testing Services & Operations ===")
        # 3.1 Report Service – Filter by hostel_type
        rep_service = ReportService(db)
        bh_reports = rep_service.list_reports(hostel_type="Boys Hostel")
        print(f"Found {len(bh_reports)} Boys Hostel complaints")
        for r in bh_reports:
            assert r.hostel_type == "Boys Hostel"

        # 3.2 Report Service – Filter by category
        food_reports = rep_service.list_reports(category="Food/Mess")
        print(f"Found {len(food_reports)} Food/Mess complaints")
        for r in food_reports:
            assert r.category == "Food/Mess"

        # 3.3 Create a new complaint via ReportService
        resident = db.query(User).filter(User.role == "student").first()
        warden = db.query(User).filter(User.role == "warden").first()
        new_complaint = rep_service.create_report(
            reporter_id=resident.id,
            hostel_type="Boys Hostel",
            location="Block A, 1st Floor",
            category="Electrical",
            building="Block A",
            floor="1st Floor",
            area="Corridor",
            description="Flickering light bulb near room 102",
            photo_path=None,
        )
        print(f"Created Complaint #{new_complaint.id}: {new_complaint.hostel_type} / {new_complaint.category}")
        assert new_complaint.status == "Submitted"

        # 3.4 Verify Complaint (Warden)
        verified_complaint = rep_service.verify_report(new_complaint.id, warden.id, "Verified on site")
        print(f"Complaint #{verified_complaint.id} verified: status = {verified_complaint.status}")
        assert verified_complaint.status == "Verified"

        # 3.5 Assign Complaint
        assigned_complaint = rep_service.assign_report(new_complaint.id, warden.id, "Electrical Maintenance Team")
        print(f"Complaint #{assigned_complaint.id} assigned to: {assigned_complaint.assigned_team}")
        assert assigned_complaint.assigned_team == "Electrical Maintenance Team"
        assert assigned_complaint.status == "Assigned"

        # 3.6 Mark Work Completed & Resolve Complaint
        completed_complaint = rep_service.update_status(new_complaint.id, "Work Completed", warden.id, "Bulb replaced by electrician")
        assert completed_complaint.status == "Work Completed"
        resolved_complaint = rep_service.update_status(new_complaint.id, "Resolved", warden.id, "Admin confirmed and closed")
        print(f"Complaint #{resolved_complaint.id} resolved: resolved_at = {resolved_complaint.resolved_at}")
        assert resolved_complaint.status == "Resolved"
        assert resolved_complaint.resolved_at is not None

        # 3.7 Rewards Catalog Service – Filter by category
        rew_service = RewardCatalogService(db)
        canteen_rewards = rew_service.get_rewards_by_category("Canteen")
        print(f"Canteen rewards ({len(canteen_rewards)}): {[r.name for r in canteen_rewards]}")
        assert len(canteen_rewards) > 0
        for r in canteen_rewards:
            assert r.category == "Canteen"

        # 3.8 Green Token Award & Redemption Service with Voucher Generation
        tok_service = TokenAwardService(db)
        red_service = RewardRedemptionService(db)

        # Ensure student has enough balance
        bal = tok_service.token_repo.get_or_create_balance(resident.id)
        bal.balance += 50
        db.commit()

        # Redeem first canteen reward
        target_reward = canteen_rewards[0]
        redeem_result = red_service.redeem_reward(resident.id, target_reward.id)
        print(f"Redemption successful: {redeem_result['reward_name']}")
        print(f"Generated Voucher Reference: {redeem_result['voucher_reference']}")
        assert redeem_result["voucher_reference"] is not None
        assert len(redeem_result["voucher_reference"]) > 5

        # Lookup voucher as staff
        lookup_result = red_service.lookup_redemption(redeem_result["voucher_reference"])
        print(f"Staff Voucher Lookup: {lookup_result['reward_name']} [{lookup_result['reward_category']}] - Status: {lookup_result['fulfillment_status']}")
        assert lookup_result["fulfillment_status"] == "Pending"

        # Fulfill voucher
        fulfill_result = red_service.fulfill_redemption(redeem_result["voucher_reference"], warden.id)
        print(f"Voucher fulfillment: {fulfill_result['message']}")
        assert "successfully" in fulfill_result["message"]

        # 3.9 Dashboard Service
        dash_service = DashboardService(db)
        dash_data = dash_service.get_dashboard_data()
        print(f"Dashboard KPIs ({len(dash_data['kpis'])}): {[k['title'] + ': ' + str(k['value']) for k in dash_data['kpis']]}")
        assert len(dash_data["kpis"]) >= 4

        # 3.10 Test 5-Step Workflow: Routing, Verification, Token Generation, and Resolution
        print("\n=== 4. Testing 5-Step Verification & Token Generation Workflow ===")
        admin_user = db.query(User).filter(User.role == "admin").first()
        food_staff_user = db.query(User).filter(User.role == "food_staff").first()
        warden_user = db.query(User).filter(User.role == "warden").first()

        # Balance before verification
        initial_token_bal = tok_service.token_repo.get_or_create_balance(resident.id).balance

        # Step 1: Student submits 1 Food complaint and 1 Plumbing complaint
        food_complaint = rep_service.create_report(
            reporter_id=resident.id,
            hostel_type="Boys Hostel",
            location="Mess Hall A",
            category="Food/Mess",
            building="Block B",
            floor="Ground Floor",
            area="Mess Hall",
            description="Mess breakfast food quality issue reported.",
        )
        assert food_complaint.food_related is True
        assert food_complaint.status == "Submitted"

        plumbing_complaint = rep_service.create_report(
            reporter_id=resident.id,
            hostel_type="Boys Hostel",
            location="Block A, 2nd Floor",
            category="Plumbing",
            building="Block A",
            floor="2nd Floor",
            area="Washroom",
            description="Tap leakage on 2nd floor washroom.",
        )
        assert plumbing_complaint.food_related is False
        assert plumbing_complaint.status == "Submitted"

        # Step 2: Role-based Routing & Forwarding
        # Food Staff forwards Food complaint to Admin
        forwarded_food = rep_service.forward_to_admin(
            food_complaint.id,
            food_staff_user.id,
            staff_role=food_staff_user.role,
            reason="Food staff inspected and verified mess issue on site. Forwarding to Admin."
        )
        assert forwarded_food.status == "Verified by Food Staff"

        # Warden forwards Plumbing complaint to Admin
        forwarded_plumbing = rep_service.forward_to_admin(
            plumbing_complaint.id,
            warden_user.id,
            staff_role=warden_user.role,
            reason="Warden inspected washroom pipe leakage. Forwarding to Admin."
        )
        assert forwarded_plumbing.status == "Verified by Warden"

        # STEP 2B: TEST ENFORCEMENT - Admin CANNOT verify complaint before staff forwards it
        from fastapi import HTTPException
        try:
            extra_complaint = rep_service.create_report(
                reporter_id=resident.id,
                hostel_type="Boys Hostel",
                location="Block A",
                category="Electrical",
                building="Block A",
                floor="1st Floor",
                area="Corridor",
                description="Test: admin trying to verify before forward",
            )
            rep_service.admin_verify(extra_complaint.id, admin_user.id, "Premature verify")
            assert False, "Should have raised HTTPException: Admin cannot verify before staff forwards"
        except HTTPException as e:
            assert e.status_code == 400
            assert "verified and forwarded by Warden or Food Staff" in str(e.detail)
            print("Verified: Admin was correctly blocked from verifying before staff forwarding!")

        # Step 3: Admin Verifies & Green Tokens Generated (+10 for each)
        verified_food = rep_service.admin_verify(
            food_complaint.id,
            admin_user.id,
            reason="Admin approved food complaint. Tokens granted to resident."
        )
        assert verified_food.status == "Admin Verified"

        verified_plumbing = rep_service.admin_verify(
            plumbing_complaint.id,
            admin_user.id,
            reason="Admin approved plumbing complaint. Tokens granted to resident."
        )
        assert verified_plumbing.status == "Admin Verified"

        # Assert token balance increased by +20 (10 for each admin verification)
        new_token_bal = tok_service.token_repo.get_or_create_balance(resident.id).balance
        print(f"Token balance change: {initial_token_bal} -> {new_token_bal} (+{new_token_bal - initial_token_bal})")
        assert new_token_bal == initial_token_bal + 20, "Student should have earned exactly 20 tokens (10 per complaint)"

        # STEP 3B: TEST ENFORCEMENT - Admin CANNOT close/resolve complaint until Work Completed is reported
        try:
            rep_service.admin_resolve(food_complaint.id, admin_user.id, "Premature close")
            assert False, "Should have raised HTTPException because work is not completed yet"
        except HTTPException as e:
            assert e.status_code == 400
            assert "Cannot close complaint until Warden or Food Staff informs work is completed" in str(e.detail)
            print("Verified: Admin was correctly blocked from closing complaint before work completion!")

        # STEP 3C: TEST ENFORCEMENT - Warden/FoodStaff CANNOT mark work complete before Admin verifies
        # (extra_complaint is still in 'Submitted' status, not 'Admin Verified')
        try:
            rep_service.complete_work(extra_complaint.id, warden_user.id, staff_role="warden", reason="Premature work completion")
            assert False, "Should have raised HTTPException: staff cannot complete work before Admin verifies"
        except HTTPException as e:
            assert e.status_code == 400
            assert "Work completion can only be reported for Admin Verified complaints" in str(e.detail)
            print("Verified: Staff was correctly blocked from marking work complete before Admin verification!")

        # Step 4: Issue returns to Staff/Warden -> Mark Work Completed & Report to Admin
        work_food = rep_service.complete_work(
            food_complaint.id,
            food_staff_user.id,
            staff_role=food_staff_user.role,
            reason="Kitchen staff adjusted cooking temperature and replaced batch."
        )
        assert work_food.status == "Work Completed"

        work_plumbing = rep_service.complete_work(
            plumbing_complaint.id,
            warden_user.id,
            staff_role=warden_user.role,
            reason="Plumber replaced leaking valve. Tap functioning properly."
        )
        assert work_plumbing.status == "Work Completed"

        # Step 5: Admin Final Closure -> Resolved with resolved_at timestamp
        resolved_food = rep_service.admin_resolve(
            food_complaint.id,
            admin_user.id,
            "Admin confirmed final resolution. Case closed."
        )
        assert resolved_food.status == "Resolved"
        assert resolved_food.resolved_at is not None

        resolved_plumbing = rep_service.admin_resolve(
            plumbing_complaint.id,
            admin_user.id,
            "Admin confirmed final plumbing repair. Case closed."
        )
        assert resolved_plumbing.status == "Resolved"
        assert resolved_plumbing.resolved_at is not None

        print(">>> 5-STEP WORKFLOW & TOKEN GENERATION VERIFIED SUCCESSFULLY! <<<")

        print("\n=======================================================")
        print(">>> ALL HOSTELCARE SERVICES AND LOGIC VERIFIED 100% OK! <<<")
        print("=======================================================")

    finally:
        db.close()

if __name__ == "__main__":
    test_hostelcare_backend()
