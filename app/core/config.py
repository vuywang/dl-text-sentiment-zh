from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = "基于深度学习的中文文本情感分析系统"
    CONDA_ENV_NAME: str = "zh_sentiment_fastapi"
    PYTHON_VERSION: str = "3.14.3"
    PRETRAINED_MODEL_NAME: str = "google-bert/bert-base-chinese"
    DATASET_NAME: str = "ChnSentiCorp"
    DATASET_HF_ID: str = "lansinuote/ChnSentiCorp"
    SQLITE_TOOL_DIR: str = r"C:\soft\sqlite-tools-win-x64-3530000"
    DEFAULT_MAX_LENGTH: int = 128

    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    APP_DIR: Path = ROOT_DIR / "app"
    STATIC_DIR: Path = ROOT_DIR / "static"
    STORAGE_DIR: Path = ROOT_DIR / "storage"
    DB_DIR: Path = STORAGE_DIR / "db"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    EXPORT_DIR: Path = STORAGE_DIR / "exports"
    LOG_DIR: Path = STORAGE_DIR / "logs"
    MODEL_DIR: Path = STORAGE_DIR / "models"
    CURRENT_MODEL_DIR: Path = MODEL_DIR / "current"
    ARCHIVE_MODEL_DIR: Path = MODEL_DIR / "archive"
    DATASET_DIR: Path = STORAGE_DIR / "datasets"

    @property
    def DB_PATH(self) -> Path:
        return self.DB_DIR / "app.db"

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"sqlite:///{self.DB_PATH.as_posix()}"


settings = Settings()


def ensure_directories() -> None:
    for path in [
        settings.STATIC_DIR,
        settings.STATIC_DIR / "css",
        settings.STATIC_DIR / "js",
        settings.STATIC_DIR / "img",
        settings.DB_DIR,
        settings.UPLOAD_DIR,
        settings.EXPORT_DIR,
        settings.LOG_DIR,
        settings.CURRENT_MODEL_DIR,
        settings.ARCHIVE_MODEL_DIR,
        settings.DATASET_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
