import json
from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db.model_registry import ModelRegistry
from app.models.db.train_task import TrainTask
from app.services.history_service import latest_completed_train_task, train_task_to_dict
from app.services.model_service import list_models, model_to_dict
from app.utils.file_utils import display_path, resolve_storage_path, storage_url

LOSS_LINE_PATTERN = re.compile(
    r"epoch=(?P<epoch>\d+),\s*train_loss=(?P<train_loss>[0-9.]+),\s*val_loss=(?P<val_loss>[0-9.]+)",
)


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


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_metric(value: object) -> float | None:
    numeric = _as_float(value)
    if numeric is None:
        return None
    return round(numeric, 4)


def _normalize_series(value: object) -> list[float]:
    if not isinstance(value, list):
        return []
    items: list[float] = []
    for item in value:
        numeric = _as_float(item)
        if numeric is not None:
            items.append(round(numeric, 6))
    return items


def _candidate_log_paths(task_id: int) -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()

    for path in [
        settings.LOG_DIR / f"train_task_{task_id}.log",
        settings.LOG_DIR / f"train_task_{task_id}_manual.log",
        *sorted(settings.LOG_DIR.glob(f"train_task_{task_id}*.log")),
    ]:
        if path.name.endswith(".err.log"):
            continue
        key = str(path.resolve())
        if key in seen or not path.exists():
            continue
        seen.add(key)
        candidates.append(path)

    return candidates


def _series_from_log(task_id: int) -> tuple[list[float], list[float]]:
    for path in _candidate_log_paths(task_id):
        epoch_map: dict[int, tuple[float, float]] = {}
        with path.open("r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                matched = LOSS_LINE_PATTERN.search(line)
                if matched is None:
                    continue
                epoch = int(matched.group("epoch"))
                train_loss = float(matched.group("train_loss"))
                val_loss = float(matched.group("val_loss"))
                epoch_map[epoch] = (train_loss, val_loss)

        if epoch_map:
            train_losses = [round(epoch_map[index][0], 6) for index in sorted(epoch_map)]
            val_losses = [round(epoch_map[index][1], 6) for index in sorted(epoch_map)]
            return train_losses, val_losses

    return [], []


def _resolve_path(path_value: object, fallback: Path | None = None) -> str | None:
    if isinstance(path_value, str) and path_value.strip():
        resolved = display_path(path_value)
        return resolved or path_value
    if fallback is not None:
        resolved = display_path(fallback)
        return resolved or str(fallback)
    return None


def _safe_division(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _safe_f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _build_classification_report(
    confusion_matrix: list[list[int]],
    accuracy: float | None,
    precision_score: float | None,
    recall_score: float | None,
    f1_score: float | None,
) -> list[dict[str, object]]:
    if len(confusion_matrix) != 2 or any(len(row) != 2 for row in confusion_matrix):
        return []

    negative_true = int(confusion_matrix[0][0])
    negative_false = int(confusion_matrix[0][1])
    positive_false = int(confusion_matrix[1][0])
    positive_true = int(confusion_matrix[1][1])

    negative_precision = _safe_division(negative_true, negative_true + positive_false)
    negative_recall = _safe_division(negative_true, negative_true + negative_false)
    positive_precision = _safe_division(positive_true, positive_true + negative_false)
    positive_recall = _safe_division(positive_true, positive_true + positive_false)

    total_support = negative_true + negative_false + positive_false + positive_true
    overall_precision = precision_score if precision_score is not None else positive_precision
    overall_recall = recall_score if recall_score is not None else positive_recall
    overall_f1 = f1_score if f1_score is not None else _safe_f1(overall_precision, overall_recall)

    return [
        {
            "label": "消极",
            "precision": round(negative_precision, 4),
            "recall": round(negative_recall, 4),
            "f1_score": round(_safe_f1(negative_precision, negative_recall), 4),
            "support": negative_true + negative_false,
        },
        {
            "label": "积极",
            "precision": round(positive_precision, 4),
            "recall": round(positive_recall, 4),
            "f1_score": round(_safe_f1(positive_precision, positive_recall), 4),
            "support": positive_false + positive_true,
        },
        {
            "label": "整体",
            "precision": round(overall_precision or 0.0, 4),
            "recall": round(overall_recall or 0.0, 4),
            "f1_score": round(overall_f1 or 0.0, 4),
            "support": total_support,
            "accuracy": round(accuracy or 0.0, 4),
        },
    ]


def _model_metrics_payload(model: ModelRegistry, train_task: TrainTask | None) -> dict[str, object]:
    model_dir = resolve_storage_path(model.model_dir)
    metrics = _read_json(model_dir / "metrics.json" if model_dir else None)
    accuracy = _first_defined(train_task.accuracy if train_task else None, metrics.get("accuracy"))
    precision = _first_defined(train_task.precision_score if train_task else None, metrics.get("precision_score"))
    recall = _first_defined(train_task.recall_score if train_task else None, metrics.get("recall_score"))
    f1_score = _first_defined(train_task.f1_score if train_task else None, metrics.get("f1_score"))
    confusion_path = _resolve_path(metrics.get("confusion_matrix_path"), model_dir / "confusion_matrix.png" if model_dir else None)
    loss_path = _resolve_path(metrics.get("loss_curve_path"), model_dir / "loss_curve.png" if model_dir else None)
    return {
        **model_to_dict(model),
        "accuracy": _round_metric(accuracy),
        "precision": _round_metric(precision),
        "precision_score": _round_metric(precision),
        "recall": _round_metric(recall),
        "recall_score": _round_metric(recall),
        "f1_score": _round_metric(f1_score),
        "remark": model.remark,
        "confusion_matrix_path": confusion_path,
        "loss_curve_path": loss_path,
        "confusion_matrix_url": storage_url(confusion_path),
        "loss_curve_url": storage_url(loss_path),
    }


def list_model_comparison(db: Session) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for model in list_models(db):
        train_task = _find_train_task_for_model(db, model)
        items.append(_model_metrics_payload(model, train_task))
    return items


def get_latest_evaluation(db: Session) -> dict[str, object]:
    latest_task = latest_completed_train_task(db)
    comparison_models = list_model_comparison(db)

    if latest_task is None:
        return {
            "latest_task": None,
            "accuracy": None,
            "precision_score": None,
            "recall_score": None,
            "f1_score": None,
            "train_loss": None,
            "val_loss": None,
            "train_losses": [],
            "val_losses": [],
            "confusion_matrix": [],
            "confusion_matrix_path": None,
            "loss_curve_path": None,
            "confusion_matrix_url": None,
            "loss_curve_url": None,
            "model_name": None,
            "dataset_name": None,
            "epoch_count": None,
            "batch_size": None,
            "learning_rate": None,
            "max_length": None,
            "created_at": None,
            "finished_at": None,
            "classification_report": [],
            "train_config": {},
            "model_comparison": comparison_models,
        }

    model_dir = resolve_storage_path(latest_task.model_dir) if latest_task.model_dir else None
    metrics = _read_json(model_dir / "metrics.json" if model_dir else None)
    train_config = _read_json(model_dir / "train_config.json" if model_dir else None)

    accuracy = _round_metric(_first_defined(metrics.get("accuracy"), latest_task.accuracy))
    precision_score = _round_metric(_first_defined(metrics.get("precision_score"), latest_task.precision_score))
    recall_score = _round_metric(_first_defined(metrics.get("recall_score"), latest_task.recall_score))
    f1_score = _round_metric(_first_defined(metrics.get("f1_score"), latest_task.f1_score))
    train_loss = _round_metric(_first_defined(metrics.get("train_loss"), latest_task.train_loss))
    val_loss = _round_metric(_first_defined(metrics.get("val_loss"), latest_task.val_loss))
    train_losses = _normalize_series(metrics.get("train_losses"))
    val_losses = _normalize_series(metrics.get("val_losses"))
    loss_series_source = "metrics" if train_losses and val_losses else None
    if not train_losses or not val_losses:
        train_losses, val_losses = _series_from_log(latest_task.id)
        if train_losses and val_losses:
            loss_series_source = "log"

    confusion_matrix = metrics.get("confusion_matrix", [])
    if not isinstance(confusion_matrix, list):
        confusion_matrix = []

    confusion_fallback = resolve_storage_path(latest_task.confusion_matrix_path) if latest_task.confusion_matrix_path else None
    confusion_path = _resolve_path(
        metrics.get("confusion_matrix_path"),
        confusion_fallback or (model_dir / "confusion_matrix.png" if model_dir else None),
    )
    loss_path = _resolve_path(metrics.get("loss_curve_path"), model_dir / "loss_curve.png" if model_dir else None)

    return {
        "latest_task": train_task_to_dict(latest_task),
        "accuracy": accuracy,
        "precision_score": precision_score,
        "recall_score": recall_score,
        "f1_score": f1_score,
        "train_loss": train_loss,
        "val_loss": val_loss,
        "train_losses": train_losses,
        "val_losses": val_losses,
        "loss_series_source": loss_series_source,
        "confusion_matrix": confusion_matrix,
        "confusion_matrix_path": confusion_path,
        "loss_curve_path": loss_path,
        "confusion_matrix_url": storage_url(confusion_path),
        "loss_curve_url": storage_url(loss_path),
        "model_name": latest_task.model_name,
        "dataset_name": latest_task.dataset_name,
        "epoch_count": int(latest_task.epoch_count),
        "batch_size": int(latest_task.batch_size),
        "learning_rate": float(latest_task.learning_rate),
        "max_length": int(latest_task.max_length),
        "created_at": latest_task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": latest_task.finished_at.strftime("%Y-%m-%d %H:%M:%S") if latest_task.finished_at else None,
        "classification_report": _build_classification_report(
            confusion_matrix,
            accuracy,
            precision_score,
            recall_score,
            f1_score,
        ),
        "train_config": train_config,
        "metric_cards": {
            "accuracy": accuracy,
            "precision": precision_score,
            "recall": recall_score,
            "f1_score": f1_score,
            "train_loss": train_loss,
            "val_loss": val_loss,
        },
        "loss_series": {
            "train_losses": train_losses,
            "val_losses": val_losses,
        },
        "model_comparison": comparison_models,
        "model_info": {
            "model_name": latest_task.model_name,
            "model_dir": display_path(latest_task.model_dir) or latest_task.model_dir,
            "dataset_name": latest_task.dataset_name,
            "pretrained_model": train_config.get("pretrained_model"),
        },
    }
