import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.db.model_registry import ModelRegistry
from app.models.db.train_task import TrainTask
from app.services.history_service import latest_completed_train_task, train_task_to_dict
from app.services.model_service import get_active_model, list_models, model_to_dict, predict_text
from app.utils.file_utils import storage_url

SAMPLE_TEXTS = [
    "这家店的服务很好，菜品也很新鲜。",
    "电影节奏拖沓，剧情也很无聊。",
    "物流速度很快，包装完整。",
    "客服态度不好，问题一直没有解决。",
    "整体体验不错，下次还会购买。",
]


def _read_json(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def _find_train_task_for_model(db: Session, model: ModelRegistry) -> TrainTask | None:
    return (
        db.query(TrainTask)
        .filter(TrainTask.model_name == model.model_name)
        .order_by(TrainTask.created_at.desc())
        .first()
    )


def _first_defined(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _model_metrics_payload(model: ModelRegistry, train_task: TrainTask | None) -> dict[str, object]:
    model_dir = Path(model.model_dir)
    metrics = _read_json(model_dir / "metrics.json")
    accuracy = _first_defined(train_task.accuracy if train_task else None, metrics.get("accuracy"))
    precision = _first_defined(train_task.precision_score if train_task else None, metrics.get("precision_score"))
    recall = _first_defined(train_task.recall_score if train_task else None, metrics.get("recall_score"))
    f1_score = _first_defined(train_task.f1_score if train_task else None, metrics.get("f1_score"))
    return {
        **model_to_dict(model),
        "accuracy": round(float(accuracy), 4) if accuracy is not None else None,
        "precision": round(float(precision), 4) if precision is not None else None,
        "recall": round(float(recall), 4) if recall is not None else None,
        "f1_score": round(float(f1_score), 4) if f1_score is not None else None,
        "remark": model.remark,
        "confusion_matrix_url": storage_url(metrics.get("confusion_matrix_path") or (model_dir / "confusion_matrix.png")),
        "loss_curve_url": storage_url(metrics.get("loss_curve_path") or (model_dir / "loss_curve.png")),
    }


def list_model_comparison(db: Session) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for model in list_models(db):
        train_task = _find_train_task_for_model(db, model)
        items.append(_model_metrics_payload(model, train_task))
    return items


def get_latest_evaluation(db: Session) -> dict[str, object]:
    latest_task = latest_completed_train_task(db)
    active_model = get_active_model(db)
    comparison_models = list_model_comparison(db)

    if latest_task is None:
        return {
            "latest_task": None,
            "metric_cards": None,
            "confusion_matrix": [],
            "confusion_matrix_url": None,
            "loss_curve_url": None,
            "loss_series": {"train_losses": [], "val_losses": []},
            "sample_predictions": [],
            "sample_prediction_model": active_model.model_name if active_model else None,
            "model_comparison": comparison_models,
        }

    metrics_path = Path(latest_task.model_dir) / "metrics.json" if latest_task.model_dir else None
    config_path = Path(latest_task.model_dir) / "train_config.json" if latest_task.model_dir else None
    metrics = _read_json(metrics_path)
    train_config = _read_json(config_path)
    sample_predictions: list[dict[str, object]] = []

    for text in SAMPLE_TEXTS:
        try:
            prediction = predict_text(text, db, max_length=int(train_config.get("max_length", 128)))
            sample_predictions.append({"text": text, **prediction})
        except Exception as exc:  # noqa: BLE001
            sample_predictions.append({"text": text, "error": str(exc)})

    return {
        "latest_task": train_task_to_dict(latest_task),
        "metric_cards": {
            "accuracy": round(float(latest_task.accuracy or 0.0), 4),
            "precision": round(float(latest_task.precision_score or 0.0), 4),
            "recall": round(float(latest_task.recall_score or 0.0), 4),
            "f1_score": round(float(latest_task.f1_score or 0.0), 4),
            "train_loss": round(float(latest_task.train_loss or 0.0), 4) if latest_task.train_loss is not None else None,
            "val_loss": round(float(latest_task.val_loss or 0.0), 4) if latest_task.val_loss is not None else None,
        },
        "confusion_matrix": metrics.get("confusion_matrix", []),
        "confusion_matrix_url": storage_url(
            metrics.get("confusion_matrix_path") or latest_task.confusion_matrix_path
        ),
        "loss_curve_url": storage_url(metrics.get("loss_curve_path") or (Path(latest_task.model_dir) / "loss_curve.png")),
        "loss_series": {
            "train_losses": metrics.get("train_losses", []),
            "val_losses": metrics.get("val_losses", []),
        },
        "train_config": train_config,
        "sample_predictions": sample_predictions,
        "sample_prediction_model": active_model.model_name if active_model else latest_task.model_name,
        "model_comparison": comparison_models,
    }
