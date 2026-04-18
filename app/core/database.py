from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import ensure_directories, settings

ensure_directories()

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    __abstract__ = True


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models.db  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_db()


def migrate_db() -> None:
    """Apply small SQLite-safe migrations for existing local databases."""
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(analysis_record)")).fetchall()
        }
        if not columns:
            return
        if "source_type" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE analysis_record "
                    "ADD COLUMN source_type VARCHAR(20) NOT NULL DEFAULT 'single'"
                )
            )
        if "batch_task_id" not in columns:
            connection.execute(text("ALTER TABLE analysis_record ADD COLUMN batch_task_id INTEGER"))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_analysis_record_source_type "
                "ON analysis_record (source_type)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_analysis_record_batch_task_id "
                "ON analysis_record (batch_task_id)"
            )
        )
