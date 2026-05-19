from sqlalchemy.orm import Session

from app.models.db.analysis_record import AnalysisRecord
from app.services.predict_service import record_to_dict
from app.utils.text_utils import clean_text


def confidence_status(confidence: float) -> str:
    if confidence >= 0.8:
        return "高可信"
    if confidence >= 0.6:
        return "一般可信"
    return "建议复核"


def list_low_confidence_records(db: Session, limit: int = 200) -> dict[str, object]:
    records = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.confidence < 0.6)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    positive_count = 0
    negative_count = 0
    confidence_sum = 0.0
    for record in records:
        item = {
            **record_to_dict(record),
            "review_status": confidence_status(float(record.confidence)),
            "status": confidence_status(float(record.confidence)),
        }
        items.append(item)
        confidence_sum += float(record.confidence)
        if record.predicted_label == "积极":
            positive_count += 1
        else:
            negative_count += 1

    return {
        "items": items,
        "summary": {
            "total_count": len(items),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "average_confidence": round(confidence_sum / len(items), 4) if items else 0.0,
        },
    }


def _possible_reason(text: str, confidence: float) -> str:
    reasons: list[str] = []
    if any(keyword in text for keyword in ("不", "没", "无", "不是", "并非")):
        reasons.append("否定表达")
    if any(keyword in text for keyword in ("但是", "不过", "然而", "可是", "却")):
        reasons.append("转折表达")
    if len(clean_text(text)) <= 8:
        reasons.append("短文本语义不足")
    if confidence < 0.6:
        reasons.append("情感倾向不明显")
    if not reasons:
        reasons.append("情感表达复杂")
    return "、".join(reasons[:2])


def generate_error_samples(db: Session, limit: int = 20, scan_limit: int = 200) -> dict[str, object]:
    records = (
        db.query(AnalysisRecord)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(scan_limit)
        .all()
    )

    items: list[dict[str, object]] = []
    for record in records:
        confidence = float(record.confidence)
        reason = _possible_reason(record.input_text, confidence)
        should_include = confidence < 0.8 or reason != "情感表达复杂"
        if not should_include:
            continue
        items.append(
            {
                "id": record.id,
                "input_text": record.input_text,
                "predicted_label": record.predicted_label,
                "confidence": confidence,
                "possible_reason": reason,
                "positive_score": float(record.positive_score),
                "negative_score": float(record.negative_score),
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "source_type": record.source_type,
            }
        )
        if len(items) >= limit:
            break

    message = (
        "中文情感分析中，否定、转折、反讽、短文本和情感混合表达容易影响模型判断，因此系统对低置信度和疑似难判样本进行展示分析。"
        if items
        else "当前没有可展示的疑似误判或难判样本，页面会以空状态展示。"
    )

    return {
        "items": items,
        "summary": {
            "scan_count": len(records),
            "error_count": len(items),
            "message": message,
        },
    }
