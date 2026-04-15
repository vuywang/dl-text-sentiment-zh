from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.db.analysis_record import AnalysisRecord
from app.models.db.batch_task import BatchTask
from app.models.db.train_task import TrainTask
from app.services.predict_service import record_to_dict
from app.utils.time_utils import format_datetime


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
        "created_at": format_datetime(task.created_at),
    }


def train_task_to_dict(task: TrainTask) -> dict[str, object]:
    return {
        "id": task.id,
        "model_name": task.model_name,
        "dataset_name": task.dataset_name,
        "epoch_count": task.epoch_count,
        "batch_size": task.batch_size,
        "learning_rate": task.learning_rate,
        "max_length": task.max_length,
        "train_loss": task.train_loss,
        "val_loss": task.val_loss,
        "accuracy": task.accuracy,
        "precision_score": task.precision_score,
        "recall_score": task.recall_score,
        "f1_score": task.f1_score,
        "confusion_matrix_path": task.confusion_matrix_path,
        "model_dir": task.model_dir,
        "status": task.status,
        "created_at": format_datetime(task.created_at),
        "finished_at": format_datetime(task.finished_at),
    }


def list_analysis_records(db: Session, limit: int = 100) -> list[dict[str, object]]:
    records = (
        db.query(AnalysisRecord)
        .order_by(AnalysisRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [record_to_dict(record) for record in records]


def list_batch_tasks(db: Session, limit: int = 100) -> list[dict[str, object]]:
    tasks = db.query(BatchTask).order_by(BatchTask.created_at.desc()).limit(limit).all()
    return [batch_task_to_dict(task) for task in tasks]


def list_train_tasks(db: Session, limit: int = 100) -> list[dict[str, object]]:
    tasks = db.query(TrainTask).order_by(TrainTask.created_at.desc()).limit(limit).all()
    return [train_task_to_dict(task) for task in tasks]


def recent_train_tasks(db: Session, limit: int = 5) -> list[dict[str, object]]:
    return list_train_tasks(db, limit)


def recent_analysis_records(db: Session, limit: int = 10) -> list[dict[str, object]]:
    return list_analysis_records(db, limit)


def latest_completed_train_task(db: Session) -> TrainTask | None:
    return (
        db.query(TrainTask)
        .filter(TrainTask.status == "completed")
        .order_by(TrainTask.finished_at.desc(), TrainTask.created_at.desc())
        .first()
    )


def sentiment_statistics(db: Session) -> dict[str, int]:
    positive_count = (
        db.query(func.count(AnalysisRecord.id))
        .filter(AnalysisRecord.predicted_label == "积极")
        .scalar()
        or 0
    )
    negative_count = (
        db.query(func.count(AnalysisRecord.id))
        .filter(AnalysisRecord.predicted_label == "消极")
        .scalar()
        or 0
    )
    total_count = positive_count + negative_count
    return {
        "total_count": total_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
    }
