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
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        users = [
            User(
                username="admin",
                email="admin@campus.edu",
                hashed_password=hash_password("admin123"),
                full_name="Admin User",
                role="admin",
            ),
            User(
                username="maintenance1",
                email="maintenance@campus.edu",
                hashed_password=hash_password("maint123"),
                full_name="Rajesh Kumar",
                role="maintenance",
            ),
            User(
                username="student1",
                email="student1@campus.edu",
                hashed_password=hash_password("student123"),
                full_name="Priya Sharma",
                role="student",
            ),
            User(
                username="student2",
                email="student2@campus.edu",
                hashed_password=hash_password("student123"),
                full_name="Amit Patel",
                role="student",
            ),
            User(
                username="student3",
                email="student3@campus.edu",
                hashed_password=hash_password("student123"),
                full_name="Sneha Reddy",
                role="student",
            ),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        locations = [
            ("Block A, Ground Floor", "Block A", "Ground", "Lobby"),
            ("Block B, 2nd Floor", "Block B", "2nd", "Corridor"),
            ("Library, 1st Floor", "Library", "1st", "Reading Room"),
            ("Cafeteria", "Canteen", "Ground", "Dining Area"),
            ("Hostel C, 3rd Floor", "Hostel C", "3rd", "Washroom"),
            ("Admin Building", "Admin", "Ground", "Entrance"),
            ("Sports Complex", "Sports", "Ground", "Gym"),
            ("Block D, 1st Floor", "Block D", "1st", "Lab"),
        ]

        statuses = ["Submitted", "Verified", "In Progress", "Resolved", "Rejected"]
        students = [u for u in users if u.role == "student"]

        reports = []
        for i, (loc, bld, flr, area) in enumerate(locations):
            status = statuses[i % len(statuses)]
            days_ago = random.randint(1, 14)
            report = Report(
                reporter_id=students[i % len(students)].id,
                photo_path=f"uploads/report_{i+1}.jpg",
                location=loc,
                building=bld,
                floor=flr,
                area=area,
                description=f"Report {i+1}: Maintenance issue at {loc}",
                status=status,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
                updated_at=datetime.utcnow() - timedelta(days=max(0, days_ago - 2)),
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            reports.append(report)

        maintenance_user = [u for u in users if u.role == "maintenance"][0]
        for report in reports:
            if report.status != "Submitted":
                history = ReportStatusHistory(
                    report_id=report.id,
                    from_status="Submitted",
                    to_status="Verified",
                    changed_by_id=maintenance_user.id,
                    changed_at=report.created_at + timedelta(hours=2),
                )
                db.add(history)

            if report.status in ["In Progress", "Resolved"]:
                history = ReportStatusHistory(
                    report_id=report.id,
                    from_status="Verified",
                    to_status="In Progress",
                    changed_by_id=maintenance_user.id,
                    changed_at=report.created_at + timedelta(days=1),
                )
                db.add(history)

            if report.status == "Resolved":
                history = ReportStatusHistory(
                    report_id=report.id,
                    from_status="In Progress",
                    to_status="Resolved",
                    changed_by_id=maintenance_user.id,
                    changed_at=report.created_at + timedelta(days=3),
                )
                db.add(history)

            if report.status == "Rejected":
                history = ReportStatusHistory(
                    report_id=report.id,
                    from_status="Submitted",
                    to_status="Rejected",
                    changed_by_id=maintenance_user.id,
                    reason="Insufficient information in report",
                    changed_at=report.created_at + timedelta(hours=1),
                )
                db.add(history)

        db.commit()

        for student in students:
            balance = TokenBalance(student_id=student.id, balance=0)
            db.add(balance)
        db.commit()

        rewards = [
            RewardCatalogItem(name="Canteen Meal Voucher", description="Free meal at campus canteen", token_cost=30, category="canteen"),
            RewardCatalogItem(name="Coffee Voucher", description="Free coffee at campus cafe", token_cost=10, category="canteen"),
            RewardCatalogItem(name="Printing Credits (50 pages)", description="50 pages of printing", token_cost=15, category="printing"),
            RewardCatalogItem(name="Stationery Kit", description="Pens, pencils, and notebook", token_cost=20, category="merchandise"),
            RewardCatalogItem(name="Campus Hoodie", description="Official campus hoodie", token_cost=50, category="merchandise"),
            RewardCatalogItem(name="Bus Pass (Weekly)", description="One week unlimited campus bus", token_cost=25, category="transport"),
        ]
        db.add_all(rewards)
        db.commit()

        print(f"Seeded {len(users)} users, {len(reports)} reports, {len(rewards)} rewards")
        print("Login credentials:")
        print("  admin / admin123 (Admin)")
        print("  maintenance1 / maint123 (Maintenance)")
        print("  student1 / student123 (Student)")
        print("  student2 / student123 (Student)")
        print("  student3 / student123 (Student)")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
