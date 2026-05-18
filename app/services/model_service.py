from pathlib import Path
from threading import Lock
from typing import Any

import torch
from sqlalchemy.orm import Session
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models.db.model_registry import ModelRegistry

logger = get_logger(__name__)

_model_lock = Lock()
_tokenizer: Any | None = None
_model: Any | None = None
_device: torch.device | None = None
_active_marker: str | None = None
_active_name: str | None = None


def get_active_model(db: Session) -> ModelRegistry | None:
    return db.query(ModelRegistry).filter(ModelRegistry.is_active.is_(True)).first()


def list_models(db: Session) -> list[ModelRegistry]:
    return db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()


def model_to_dict(model: ModelRegistry) -> dict[str, object]:
    return {
        "id": model.id,
        "model_name": model.model_name,
        "model_type": model.model_type,
        "model_dir": model.model_dir,
        "is_active": model.is_active,
        "remark": model.remark,
        "created_at": model.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _save_base_model(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(settings.PRETRAINED_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        settings.PRETRAINED_MODEL_NAME,
        num_labels=2,
    )
    tokenizer.save_pretrained(base_dir)
    model.save_pretrained(base_dir)


def ensure_default_model(db: Session) -> ModelRegistry:
    active = get_active_model(db)
    if active is not None:
        return active

    existing = db.query(ModelRegistry).order_by(ModelRegistry.id.asc()).first()
    if existing is not None:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    base_dir = settings.CURRENT_MODEL_DIR / "bert-base-chinese-base"
    remark = "未微调基础模型，来源 google-bert/bert-base-chinese，分类头按二分类任务初始化。"
    if not (base_dir / "config.json").exists():
        try:
            _save_base_model(base_dir)
            remark = "未微调基础模型已保存到本地 current 目录。"
        except Exception as exc:  # noqa: BLE001
            base_dir.mkdir(parents=True, exist_ok=True)
            logger.exception("基础模型初始化失败，推理时继续从预训练模型名称加载：%s", exc)
            remark = "未微调基础模型，本地文件未完整保存，推理时从预训练模型名称加载。"

    registry = ModelRegistry(
        model_name="bert-base-chinese-base-unfinetuned",
        model_type="base",
        model_dir=str(base_dir),
        is_active=True,
        remark=remark,
    )
    db.add(registry)
    db.commit()
    db.refresh(registry)
    return registry


def _resolve_model_source(model_info: ModelRegistry) -> str:
    model_dir = Path(model_info.model_dir)
    if (model_dir / "config.json").exists():
        return str(model_dir)
    return settings.PRETRAINED_MODEL_NAME


def load_active_model(db: Session) -> str:
    global _active_marker, _active_name, _device, _model, _tokenizer

    active = ensure_default_model(db)
    model_source = _resolve_model_source(active)
    marker = f"{active.id}:{active.model_dir}:{model_source}"

    with _model_lock:
        if _model is not None and _tokenizer is not None and _active_marker == marker:
            return active.model_name

        logger.info("加载当前激活模型：%s", model_source)
        tokenizer = AutoTokenizer.from_pretrained(model_source)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_source,
            num_labels=2,
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        _tokenizer = tokenizer
        _model = model
        _device = device
        _active_marker = marker
        _active_name = active.model_name
        return active.model_name


def load_active_model_safely() -> None:
    db = SessionLocal()
    try:
        load_active_model(db)
    except Exception as exc:  # noqa: BLE001
        logger.exception("应用启动时模型加载失败：%s", exc)
    finally:
        db.close()


def activate_model(db: Session, model_id: int) -> dict[str, object]:
    target = db.get(ModelRegistry, model_id)
    if target is None:
        raise ValueError("模型不存在")

    previous = get_active_model(db)
    previous_id = previous.id if previous is not None else None
    if target.is_active:
        load_active_model(db)
        return model_to_dict(target)

    db.query(ModelRegistry).update({ModelRegistry.is_active: False})
    target.is_active = True
    db.commit()
    db.refresh(target)

    try:
        load_active_model(db)
    except Exception as exc:  # noqa: BLE001
        db.query(ModelRegistry).update({ModelRegistry.is_active: False})
        if previous_id is not None:
            previous_model = db.get(ModelRegistry, previous_id)
            if previous_model is not None:
                previous_model.is_active = True
        db.commit()
        raise RuntimeError(f"模型启用失败：{exc}") from exc

    return model_to_dict(target)


def predict_text(text: str, db: Session, max_length: int = settings.DEFAULT_MAX_LENGTH) -> dict[str, float | str]:
    global _active_name

    if not text.strip():
        raise ValueError("文本内容不能为空")

    active_name = load_active_model(db)
    if _tokenizer is None or _model is None or _device is None:
        raise RuntimeError("当前模型未加载成功")

    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length,
    )
    inputs = {key: value.to(_device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = _model(**inputs)
        scores = torch.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

    negative_score = float(scores[0])
    positive_score = float(scores[1])
    predicted_label = "积极" if positive_score >= negative_score else "消极"
    confidence = max(positive_score, negative_score)

    return {
        "predicted_label": predicted_label,
        "confidence": round(confidence, 6),
        "positive_score": round(positive_score, 6),
        "negative_score": round(negative_score, 6),
        "model_name": active_name or _active_name or "unknown",
    }
