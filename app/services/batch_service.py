from collections import Counter
from pathlib import Path
import re

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


def _save_analysis_record(
    db: Session,
    text: str,
    result: dict[str, float | str],
    batch_task_id: int,
) -> None:
    db.add(
        AnalysisRecord(
            input_text=text,
            predicted_label=str(result["predicted_label"]),
            confidence=float(result["confidence"]),
            positive_score=float(result["positive_score"]),
            negative_score=float(result["negative_score"]),
            model_name=str(result["model_name"]),
            source_type="batch",
            batch_task_id=batch_task_id,
        )
    )


def _build_batch_report(rows: list[dict[str, object]]) -> dict[str, object]:
    total_count = len(rows)
    positive_count = sum(1 for row in rows if row["predicted_label"] == "积极")
    negative_count = total_count - positive_count
    average_confidence = sum(float(row["confidence"]) for row in rows) / total_count if total_count else 0.0
    low_confidence_count = sum(1 for row in rows if float(row["confidence"]) < 0.6)
    return {
        "total_count": total_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_ratio": round(positive_count / total_count, 4) if total_count else 0.0,
        "negative_ratio": round(negative_count / total_count, 4) if total_count else 0.0,
        "average_confidence": round(average_confidence, 4),
        "low_confidence_count": low_confidence_count,
    }


def _build_confidence_distribution(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    buckets = [
        ("0.00-0.40", 0.0, 0.4),
        ("0.40-0.60", 0.4, 0.6),
        ("0.60-0.80", 0.6, 0.8),
        ("0.80-0.90", 0.8, 0.9),
        ("0.90-1.00", 0.9, 1.01),
    ]
    items: list[dict[str, object]] = []
    for label, lower, upper in buckets:
        count = 0
        for row in rows:
            confidence = float(row["confidence"])
            if lower <= confidence < upper:
                count += 1
        items.append({"range": label, "count": count})
    return items


def _build_length_distribution(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    buckets = [
        ("1-10字", 1, 10),
        ("11-20字", 11, 20),
        ("21-40字", 21, 40),
        ("41字以上", 41, 10**9),
    ]
    items: list[dict[str, object]] = []
    for label, lower, upper in buckets:
        count = 0
        for row in rows:
            text_length = len(str(row["text"]).strip())
            if lower <= text_length <= upper:
                count += 1
        items.append({"range": label, "count": count})
    return items


def _extract_keywords(rows: list[dict[str, object]], top_n: int = 10) -> list[dict[str, object]]:
    counter: Counter[str] = Counter()
    for row in rows:
        normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", " ", str(row["text"]))
        for token in normalized.split():
            if len(token) < 2:
                continue
            if re.fullmatch(r"[\u4e00-\u9fff]{5,}", token):
                for index in range(len(token) - 1):
                    counter[token[index : index + 2]] += 1
            else:
                counter[token] += 1
    return [{"word": word, "count": count} for word, count in counter.most_common(top_n)]


def _build_batch_response(task: BatchTask, rows: list[dict[str, object]]) -> dict[str, object]:
    report = _build_batch_report(rows)
    low_confidence_preview = [row for row in rows if float(row["confidence"]) < 0.6][:20]
    high_confidence_negative_preview = [
        row
        for row in rows
        if row["predicted_label"] == "消极" and float(row["confidence"]) >= 0.8
    ][:20]

    return {
        "task": batch_task_to_dict(task),
        "preview": rows[:200],
        "preview_limit": 200,
        "chart": [
            {"name": "积极", "value": int(report["positive_count"])},
            {"name": "消极", "value": int(report["negative_count"])},
        ],
        "report": report,
        "confidence_distribution": _build_confidence_distribution(rows),
        "length_distribution": _build_length_distribution(rows),
        "top_words": _extract_keywords(rows),
        "low_confidence_preview": low_confidence_preview,
        "high_confidence_negative_preview": high_confidence_negative_preview,
    }


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
            _save_analysis_record(db, text, result, task.id)
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

        return _build_batch_response(task, rows)
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

    records = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.source_type == "batch",
            AnalysisRecord.batch_task_id == task_id,
        )
        .order_by(AnalysisRecord.id.asc())
        .all()
    )
    if records:
        rows = [
            {
                "text": record.input_text,
                "predicted_label": record.predicted_label,
                "confidence": record.confidence,
                "positive_score": record.positive_score,
                "negative_score": record.negative_score,
            }
            for record in records
        ]
    elif task.result_file_path and Path(task.result_file_path).exists():
        df = read_csv_compatible(task.result_file_path)
        rows = df.to_dict(orient="records")
    else:
        rows = []

    return _build_batch_response(task, rows)
