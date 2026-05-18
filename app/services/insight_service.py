from functools import lru_cache

from datasets import load_dataset
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db.analysis_record import AnalysisRecord
from app.services.predict_service import record_to_dict
from app.services.model_service import predict_text
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
    for record in records:
        item = {
            **record_to_dict(record),
            "status": confidence_status(float(record.confidence)),
        }
        items.append(item)
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
        },
    }


@lru_cache(maxsize=1)
def _load_eval_dataset():
    dataset = load_dataset(settings.DATASET_HF_ID, cache_dir=str(settings.DATASET_DIR))
    eval_split = "test" if "test" in dataset else "validation"
    return dataset[eval_split]


def _possible_reason(text: str, confidence: float) -> str:
    reasons: list[str] = []
    if any(keyword in text for keyword in ("但是", "不过", "然而", "却")):
        reasons.append("情感转折")
    if any(keyword in text for keyword in ("不", "没", "无", "不是", "并非")):
        reasons.append("否定表达")
    if len(clean_text(text)) <= 8:
        reasons.append("短文本语义不足")
    if confidence < 0.6:
        reasons.append("情感倾向不明显")
    if not reasons:
        reasons.append("情感表达复杂")
    return "、".join(reasons[:2])


def generate_error_samples(db: Session, limit: int = 20, scan_limit: int = 200) -> dict[str, object]:
    try:
        dataset = _load_eval_dataset()
    except Exception as exc:  # noqa: BLE001
        return {
            "items": [],
            "summary": {
                "scan_count": 0,
                "error_count": 0,
                "message": f"评估数据集加载失败：{exc}",
            },
        }

    items: list[dict[str, object]] = []
    scan_count = min(max(scan_limit, limit), len(dataset))
    for index in range(scan_count):
        row = dataset[index]
        text = str(row["text"])
        true_label = "积极" if int(row["label"]) == 1 else "消极"
        try:
            prediction = predict_text(text, db)
        except Exception as exc:  # noqa: BLE001
            return {
                "items": [],
                "summary": {
                    "scan_count": index,
                    "error_count": 0,
                    "message": f"误判样本生成失败：{exc}",
                },
            }
        if prediction["predicted_label"] == true_label:
            continue
        items.append(
            {
                "text": text,
                "true_label": true_label,
                "predicted_label": prediction["predicted_label"],
                "confidence": prediction["confidence"],
                "possible_reason": _possible_reason(text, float(prediction["confidence"])),
            }
        )
        if len(items) >= limit:
            break

    return {
        "items": items,
        "summary": {
            "scan_count": scan_count,
            "error_count": len(items),
            "message": "误判样本来自缓存评估集的抽样扫描，适合展示模型分析思路。",
        },
    }
