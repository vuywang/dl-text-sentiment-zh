import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, init_db  # noqa: E402
from app.services.model_service import ensure_default_model  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_default_model(db)
    finally:
        db.close()
    print(f"数据库初始化完成：{settings.DB_PATH}")


if __name__ == "__main__":
    main()
