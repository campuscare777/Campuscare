from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    from sqlalchemy import inspect, text
    import app.models  # Ensure models are loaded into Base metadata
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "hostel_type" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN hostel_type VARCHAR"))
        if "reports" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("reports")]
            if "verified_at" not in columns:
                conn.execute(text("ALTER TABLE reports ADD COLUMN verified_at DATETIME"))
            if "verified_by_id" not in columns:
                conn.execute(text("ALTER TABLE reports ADD COLUMN verified_by_id INTEGER REFERENCES users(id)"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
