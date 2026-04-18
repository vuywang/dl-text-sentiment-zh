from sqlalchemy.orm import Session

from app.models.db.analysis_record import AnalysisRecord
from app.services.model_service import predict_text
from app.utils.text_utils import require_text


def predict_and_save(text: str, db: Session) -> dict[str, float | str | int]:
    clean_value = require_text(text)
    result = predict_text(clean_value, db)
    record = AnalysisRecord(
        input_text=clean_value,
        predicted_label=str(result["predicted_label"]),
        confidence=float(result["confidence"]),
        positive_score=float(result["positive_score"]),
        negative_score=float(result["negative_score"]),
        model_name=str(result["model_name"]),
        source_type="single",
        batch_task_id=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {**result, "record_id": record.id}


def record_to_dict(record: AnalysisRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "input_text": record.input_text,
        "predicted_label": record.predicted_label,
        "confidence": record.confidence,
        "positive_score": record.positive_score,
        "negative_score": record.negative_score,
        "model_name": record.model_name,
        "source_type": record.source_type,
        "batch_task_id": record.batch_task_id,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
