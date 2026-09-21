import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import engine, Base, SessionLocal
from app.models.user import User
from app.models.report import Report, ReportStatusHistory
from app.models.token import TokenBalance, TokenTransaction
from app.models.reward import RewardCatalogItem
from app.services.auth_service import hash_password
from datetime import datetime, timedelta
import random


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        force_reset = "--reset" in sys.argv
        if not force_reset and db.query(User).filter(User.username == "warden1").first():
            print("HostelCare already seeded. Use --reset to re-seed.")
            return

        if force_reset:
            print("Resetting database for HostelCare clean seed...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

        print("Seeding HostelCare database...")

        # ------------------------------------------------------------------
        # Users
        # ------------------------------------------------------------------
        users = [
            User(
                username="admin",
                email="admin@hostelcare.edu",
                hashed_password=hash_password("admin123"),
                full_name="Admin User",
                role="admin",
            ),
            User(
                username="warden1",
                email="warden1@hostelcare.edu",
                hashed_password=hash_password("warden123"),
                full_name="Dr. Ramesh Iyer",
                role="warden",       # HostelCare warden role
            ),
            User(
                username="maintenance1",
                email="maintenance1@hostelcare.edu",
                hashed_password=hash_password("maint123"),
                full_name="Rajesh Kumar",
                role="maintenance",
            ),
            User(
                username="food_staff1",
                email="food1@hostelcare.edu",
                hashed_password=hash_password("food123"),
                full_name="Meena Anand",
                role="food_staff",   # Food/Mess staff role
            ),
            User(
                username="resident1",
                email="resident1@hostelcare.edu",
                hashed_password=hash_password("resident123"),
                full_name="Priya Sharma",
                role="student",      # Residents are stored as 'student' role in DB
            ),
            User(
                username="resident2",
                email="resident2@hostelcare.edu",
                hashed_password=hash_password("resident123"),
                full_name="Amit Patel",
                role="student",
            ),
            User(
                username="resident3",
                email="resident3@hostelcare.edu",
                hashed_password=hash_password("resident123"),
                full_name="Sneha Reddy",
                role="student",
            ),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        # ------------------------------------------------------------------
        # Hostel complaints – varied hostel types and categories
        # ------------------------------------------------------------------
        complaints_data = [
            # (hostel_type, location, building, floor, area, category, description)
            ("Boys Hostel",  "Block A, Ground Floor", "Block A", "Ground Floor", "Washroom",     "Plumbing",        "Water pipe leaking near washroom entrance"),
            ("Boys Hostel",  "Block B, 2nd Floor",    "Block B", "2nd Floor",    "Corridor",     "Electrical",      "Corridor light not working since 2 days"),
            ("Girls Hostel", "Block E, 1st Floor",    "Block E", "1st Floor",    "Common Room",  "Furniture",       "2 chairs broken in common room"),
            ("Girls Hostel", "Block F, 3rd Floor",    "Block F", "3rd Floor",    "Washroom",     "Cleanliness",     "Washroom floor not cleaned for 3 days"),
            ("Boys Hostel",  "Block C, Dining Area",  "Block C", "Ground Floor", "Dining Area",  "Food/Mess",       "Food quality very poor – rice undercooked"),
            ("NRI Hostel",   "NRI Wing A, 2nd Floor", "NRI Wing A", "2nd Floor", "Lobby",        "Internet/Network","WiFi not working in NRI Wing A lobby"),
            ("Boys Hostel",  "Block D, 1st Floor",    "Block D", "1st Floor",    "Study Room",   "Pest Control",    "Cockroach infestation in study room"),
            ("Girls Hostel", "Block G, Ground Floor", "Block G", "Ground Floor", "Dining Area",  "Food/Mess",       "Tea not served in the morning for 2 days"),
        ]

        statuses = ["Submitted", "Verified", "In Progress", "Resolved", "Rejected", "Submitted", "Under Review", "Assigned"]
        residents = [u for u in users if u.role == "student"]
        warden = next(u for u in users if u.role == "warden")

        reports = []
        for i, (hostel_type, loc, bld, flr, area, cat, desc) in enumerate(complaints_data):
            st = statuses[i % len(statuses)]
            days_ago = random.randint(1, 14)
            food_related = (cat == "Food/Mess")
            report = Report(
                reporter_id=residents[i % len(residents)].id,
                hostel_type=hostel_type,
                location=loc,
                building=bld,
                floor=flr,
                area=area,
                category=cat,
                food_related=food_related,
                description=desc,
                photo_path=f"uploads/complaint_{i+1}.jpg",
                status=st,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=max(0, days_ago - 2)),
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            reports.append(report)

        # ------------------------------------------------------------------
        # Status history
        # ------------------------------------------------------------------
        for report in reports:
            if report.status not in ["Submitted", "Under Review"]:
                db.add(ReportStatusHistory(
                    report_id=report.id,
                    from_status="Submitted",
                    to_status="Verified",
                    changed_by_id=warden.id,
                    reason="Complaint verified by warden",
                    changed_at=report.created_at + timedelta(hours=2),
                ))

            if report.status in ["In Progress", "Resolved", "Assigned"]:
                db.add(ReportStatusHistory(
                    report_id=report.id,
                    from_status="Verified",
                    to_status="Assigned",
                    changed_by_id=warden.id,
                    reason="Assigned to maintenance team",
                    changed_at=report.created_at + timedelta(hours=6),
                ))

            if report.status in ["In Progress", "Resolved"]:
                db.add(ReportStatusHistory(
                    report_id=report.id,
                    from_status="Assigned",
                    to_status="In Progress",
                    changed_by_id=warden.id,
                    changed_at=report.created_at + timedelta(days=1),
                ))

            if report.status == "Resolved":
                db.add(ReportStatusHistory(
                    report_id=report.id,
                    from_status="In Progress",
                    to_status="Resolved",
                    changed_by_id=warden.id,
                    changed_at=report.created_at + timedelta(days=3),
                ))

            if report.status == "Rejected":
                db.add(ReportStatusHistory(
                    report_id=report.id,
                    from_status="Submitted",
                    to_status="Rejected",
                    changed_by_id=warden.id,
                    reason="Complaint already reported by another resident",
                    changed_at=report.created_at + timedelta(hours=1),
                ))

        db.commit()

        # ------------------------------------------------------------------
        # Token balances and award transactions for verified complaints
        # ------------------------------------------------------------------
        for resident in residents:
            db.add(TokenBalance(student_id=resident.id, balance=0))
        db.commit()

        # Award tokens for each resolved/verified complaint
        for report in reports:
            if report.status in ["Verified", "Assigned", "In Progress", "Resolved"]:
                balance = db.query(TokenBalance).filter(
                    TokenBalance.student_id == report.reporter_id
                ).first()
                if balance:
                    balance.balance += 10
                    db.add(TokenTransaction(
                        student_id=report.reporter_id,
                        transaction_type="award",
                        amount=10,
                        related_report_id=report.id,
                        created_at=report.created_at + timedelta(hours=3),
                    ))
        db.commit()

        # ------------------------------------------------------------------
        # Reward catalog – Canteen / Laundry / Hostel Stores
        # ------------------------------------------------------------------
        rewards = [
            # Canteen
            RewardCatalogItem(name="Canteen Meal Voucher",    description="Free full meal at the hostel canteen",          token_cost=30, category="Canteen",       provider_location="Main Canteen"),
            RewardCatalogItem(name="Tea / Coffee Voucher",    description="Free tea or coffee at the mess counter",        token_cost=10, category="Canteen",       provider_location="Mess Counter"),
            RewardCatalogItem(name="Canteen Snack Voucher",   description="Free snack item at the hostel canteen",         token_cost=15, category="Canteen",       provider_location="Main Canteen"),
            # Laundry
            RewardCatalogItem(name="Laundry Credit (5 items)",description="5-item laundry wash at the hostel laundry",    token_cost=20, category="Laundry",       provider_location="Ground Floor Laundry"),
            RewardCatalogItem(name="Express Laundry Service", description="Same-day laundry for up to 3 items",           token_cost=25, category="Laundry",       provider_location="Ground Floor Laundry"),
            # Hostel Stores
            RewardCatalogItem(name="Stationery Kit",          description="Pens, pencils, and a notebook",                token_cost=20, category="Hostel Stores", provider_location="Hostel Store, Block A"),
            RewardCatalogItem(name="Toiletries Pack",         description="Soap, shampoo sachet, and toothpaste",         token_cost=15, category="Hostel Stores", provider_location="Hostel Store, Block A"),
            RewardCatalogItem(name="Basic Grocery Pack",      description="Instant noodles, biscuits, and a juice pack",  token_cost=25, category="Hostel Stores", provider_location="Hostel Store, Block A"),
        ]
        db.add_all(rewards)
        db.commit()

        print(f"Seeded {len(users)} users, {len(reports)} hostel complaints, {len(rewards)} rewards")
        print("\nLogin credentials:")
        print("  admin        / admin123    (Admin)")
        print("  warden1      / warden123   (Warden)")
        print("  maintenance1 / maint123    (Maintenance)")
        print("  food_staff1  / food123     (Food/Mess Staff)")
        print("  resident1    / resident123 (Resident)")
        print("  resident2    / resident123 (Resident)")
        print("  resident3    / resident123 (Resident)")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
