from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db.analysis_record import AnalysisRecord
from app.models.db.batch_task import BatchTask
from app.services.model_service import predict_text
from app.utils.file_utils import ensure_text_column, read_csv_compatible, save_upload_file
from app.utils.text_utils import require_text
from app.utils.time_utils import now_str


def _save_analysis_record(db: Session, text: str, result: dict[str, float | str]) -> None:
    db.add(
        AnalysisRecord(
            input_text=text,
            predicted_label=str(result["predicted_label"]),
            confidence=float(result["confidence"]),
            positive_score=float(result["positive_score"]),
            negative_score=float(result["negative_score"]),
            model_name=str(result["model_name"]),
        )
    )


def process_batch_upload(upload_file: UploadFile, db: Session) -> dict[str, object]:
    original_name = upload_file.filename or "upload.csv"
    saved_path = save_upload_file(upload_file)
    task = BatchTask(
        original_file_name=original_name,
        saved_file_path=str(saved_path),
        total_count=0,
        positive_count=0,
        negative_count=0,
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        df = read_csv_compatible(saved_path)
        ensure_text_column(df)
        texts: list[str] = []
        for row_index, value in enumerate(df["text"].tolist(), start=2):
            if pd.isna(value):
                raise ValueError(f"第 {row_index} 行 text 不能为空")
            texts.append(require_text(str(value)))

        rows: list[dict[str, object]] = []
        positive_count = 0
        negative_count = 0

        for text in texts:
            result = predict_text(text, db)
            _save_analysis_record(db, text, result)
            if result["predicted_label"] == "积极":
                positive_count += 1
            else:
                negative_count += 1
            rows.append(
                {
                    "text": text,
                    "predicted_label": result["predicted_label"],
                    "confidence": result["confidence"],
                    "positive_score": result["positive_score"],
                    "negative_score": result["negative_score"],
                }
            )

        result_df = pd.DataFrame(rows)
        result_path = settings.EXPORT_DIR / f"batch_result_{task.id}_{now_str()}.csv"
        result_df.to_csv(result_path, index=False, encoding="utf-8-sig")

        task.total_count = len(rows)
        task.positive_count = positive_count
        task.negative_count = negative_count
        task.result_file_path = str(result_path)
        task.status = "completed"
        db.commit()
        db.refresh(task)

        return {
            "task": batch_task_to_dict(task),
            "preview": rows[:50],
            "chart": [
                {"name": "积极", "value": positive_count},
                {"name": "消极", "value": negative_count},
            ],
        }
    except Exception:
        task.status = "failed"
        db.commit()
        raise


def batch_task_to_dict(task: BatchTask) -> dict[str, object]:
    return {
        "id": task.id,
        "original_file_name": task.original_file_name,
        "saved_file_path": task.saved_file_path,
        "total_count": task.total_count,
        "positive_count": task.positive_count,
        "negative_count": task.negative_count,
        "result_file_path": task.result_file_path,
        "status": task.status,
        "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_batch_task(db: Session, task_id: int) -> BatchTask | None:
    return db.get(BatchTask, task_id)


def get_batch_detail(db: Session, task_id: int) -> dict[str, object]:
    task = get_batch_task(db, task_id)
    if task is None:
        raise ValueError("批量任务不存在")

    preview: list[dict[str, object]] = []
    if task.result_file_path and Path(task.result_file_path).exists():
        df = read_csv_compatible(task.result_file_path)
        preview = df.head(50).to_dict(orient="records")

    return {
        "task": batch_task_to_dict(task),
        "preview": preview,
        "chart": [
            {"name": "积极", "value": task.positive_count},
            {"name": "消极", "value": task.negative_count},
        ],
    }
