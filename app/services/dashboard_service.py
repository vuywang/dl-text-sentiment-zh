from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db.analysis_record import AnalysisRecord
from app.models.db.batch_task import BatchTask
from app.services.history_service import (
    batch_task_to_dict,
    latest_completed_train_task,
    recent_analysis_records,
    recent_train_tasks,
    sentiment_statistics,
    train_task_to_dict,
)
from app.services.model_service import ensure_default_model, model_to_dict


def _recent_batch_tasks(db: Session, limit: int = 5) -> list[dict[str, object]]:
    tasks = db.query(BatchTask).order_by(BatchTask.created_at.desc()).limit(limit).all()
    return [batch_task_to_dict(task) for task in tasks]


def get_dashboard_summary(db: Session, days: int = 7) -> dict[str, object]:
    active_model = ensure_default_model(db)
    stats = sentiment_statistics(db)
    average_confidence = db.query(func.avg(AnalysisRecord.confidence)).scalar() or 0.0
    low_confidence_count = (
        db.query(func.count(AnalysisRecord.id))
        .filter(AnalysisRecord.confidence < 0.6)
        .scalar()
        or 0
    )
    latest_train = latest_completed_train_task(db)
    latest_batch = db.query(BatchTask).order_by(BatchTask.created_at.desc()).first()
    recent_records = recent_analysis_records(db, limit=8)
    recent_train = recent_train_tasks(db, limit=5)
    recent_batch = _recent_batch_tasks(db, limit=5)
    charts = get_dashboard_charts(db, days=days)
    overview = {
        **stats,
        "average_confidence": round(float(average_confidence), 4),
        "low_confidence_count": int(low_confidence_count),
    }

    return {
        "project_name": settings.PROJECT_NAME,
        "db_status": "已连接" if settings.DB_PATH.exists() else "待初始化",
        "total_count": int(overview["total_count"]),
        "positive_count": int(overview["positive_count"]),
        "negative_count": int(overview["negative_count"]),
        "average_confidence": float(overview["average_confidence"]),
        "low_confidence_count": int(overview["low_confidence_count"]),
        "active_model": model_to_dict(active_model),
        "active_model_name": active_model.model_name,
        "latest_train_task": train_task_to_dict(latest_train) if latest_train else None,
        "latest_batch_task": batch_task_to_dict(latest_batch) if latest_batch else None,
        "recent_records": recent_records,
        "sentiment_chart": charts["sentiment_chart"],
        "trend_chart": charts["trend_chart"],
        "model_metric_chart": charts["model_metric_chart"],
        "overview": overview,
        "recent_analysis_records": recent_records,
        "recent_train_tasks": recent_train,
        "recent_batch_tasks": recent_batch,
        "sentiment_ratio": charts["sentiment_chart"],
        "analysis_trend": charts["trend_chart"],
        "model_metrics": charts["model_metric_chart"],
    }


def get_dashboard_charts(db: Session, days: int = 7) -> dict[str, object]:
    stats = sentiment_statistics(db)
    latest_train = latest_completed_train_task(db)

    start_date = datetime.now() - timedelta(days=max(days - 1, 0))
    date_buckets: dict[str, dict[str, int | str]] = {}
    for index in range(days):
        current = start_date + timedelta(days=index)
        key = current.strftime("%m-%d")
        date_buckets[key] = {
            "date": key,
            "total": 0,
            "positive": 0,
            "negative": 0,
        }

    records = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.created_at >= start_date)
        .order_by(AnalysisRecord.created_at.asc())
        .all()
    )
    for record in records:
        key = record.created_at.strftime("%m-%d")
        bucket = date_buckets.setdefault(
            key,
            {"date": key, "total": 0, "positive": 0, "negative": 0},
        )
        bucket["total"] = int(bucket["total"]) + 1
        if record.predicted_label == "积极":
            bucket["positive"] = int(bucket["positive"]) + 1
        else:
            bucket["negative"] = int(bucket["negative"]) + 1

    model_metrics = None
    if latest_train is not None:
        model_metrics = {
            "model_name": latest_train.model_name,
            "accuracy": round(float(latest_train.accuracy or 0.0), 4),
            "precision_score": round(float(latest_train.precision_score or 0.0), 4),
            "recall_score": round(float(latest_train.recall_score or 0.0), 4),
            "f1_score": round(float(latest_train.f1_score or 0.0), 4),
            "precision": round(float(latest_train.precision_score or 0.0), 4),
            "recall": round(float(latest_train.recall_score or 0.0), 4),
        }

    sentiment_chart = [
        {"name": "积极", "value": int(stats["positive_count"])},
        {"name": "消极", "value": int(stats["negative_count"])},
    ]
    trend_chart = list(date_buckets.values())

    return {
        "sentiment_chart": sentiment_chart,
        "trend_chart": trend_chart,
        "model_metric_chart": model_metrics,
        "sentiment_ratio": sentiment_chart,
        "analysis_trend": trend_chart,
        "model_metrics": model_metrics,
    }
