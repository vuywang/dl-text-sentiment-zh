import re
import shutil
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from app.core.config import settings
from app.utils.time_utils import now_str


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    clean_stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5_-]+", "_", stem).strip("_")
    return f"{clean_stem or 'upload'}_{now_str()}{suffix}"


def save_upload_file(upload_file: UploadFile) -> Path:
    filename = upload_file.filename or "upload.csv"
    if Path(filename).suffix.lower() != ".csv":
        raise ValueError("只支持上传 CSV 文件")
    target_path = settings.UPLOAD_DIR / safe_filename(filename)
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return target_path


def read_csv_compatible(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(csv_path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise ValueError("CSV 编码需为 utf-8 或 utf-8-sig") from last_error
    raise ValueError("CSV 文件读取失败")


def ensure_text_column(df: pd.DataFrame) -> None:
    if "text" not in df.columns:
        raise ValueError("CSV 文件必须包含 text 列")


def resolve_storage_path(path: str | Path | None) -> Path | None:
    if not path:
        return None

    raw_path = Path(path).expanduser()
    if raw_path.exists():
        return raw_path.resolve()

    raw_parts = list(raw_path.parts)
    lower_parts = [part.lower() for part in raw_parts]

    if "storage" in lower_parts:
        storage_index = lower_parts.index("storage")
        mapped_path = settings.STORAGE_DIR.joinpath(*raw_parts[storage_index + 1 :])
        return mapped_path.resolve()

    if not raw_path.is_absolute():
        mapped_path = (settings.BASE_DIR / raw_path).resolve()
        if mapped_path.exists():
            return mapped_path

    return raw_path.resolve()


def display_path(path: str | Path | None) -> str | None:
    resolved = resolve_storage_path(path)
    return str(resolved) if resolved is not None else None


def storage_url(path: str | Path | None) -> str | None:
    resolved = resolve_storage_path(path)
    if resolved is None:
        return None
    try:
        rel_path = resolved.relative_to(settings.STORAGE_DIR.resolve())
    except ValueError:
        return None
    return "/storage/" + rel_path.as_posix()
