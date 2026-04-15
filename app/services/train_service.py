import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models.db.train_task import TrainTask
from app.models.schema.train_schema import TrainStartRequest
from app.services.history_service import train_task_to_dict
from app.services.model_service import load_active_model_safely
from app.utils.time_utils import now_str

logger = get_logger(__name__)


def start_training_task(
    params: TrainStartRequest,
    db: Session,
    background_tasks: BackgroundTasks,
) -> dict[str, object]:
    model_name = f"bert-base-chinese-finetuned-{now_str()}"
    task = TrainTask(
        model_name=model_name,
        dataset_name=settings.DATASET_NAME,
        epoch_count=params.epoch,
        batch_size=params.batch_size,
        learning_rate=params.learning_rate,
        max_length=params.max_length,
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    background_tasks.add_task(run_training_subprocess, task.id)
    return train_task_to_dict(task)


def run_training_subprocess(task_id: int) -> None:
    log_path = settings.LOG_DIR / f"train_task_{task_id}.log"
    script_path = settings.ROOT_DIR / "scripts" / "train_model.py"
    db = SessionLocal()
    task = db.get(TrainTask, task_id)
    db.close()
    if task is None:
        logger.error("训练任务不存在：%s", task_id)
        return

    cmd = [
        sys.executable,
        str(script_path),
        "--task-id",
        str(task.id),
        "--epoch",
        str(task.epoch_count),
        "--batch-size",
        str(task.batch_size),
        "--learning-rate",
        str(task.learning_rate),
        "--max-length",
        str(task.max_length),
        "--model-name",
        task.model_name,
    ]

    logger.info("启动训练脚本：%s", " ".join(cmd))
    with log_path.open("a", encoding="utf-8") as log_file:
        result = subprocess.run(
            cmd,
            cwd=settings.ROOT_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    if result.returncode == 0:
        logger.info("训练任务完成：%s", task_id)
        load_active_model_safely()
        return

    logger.error("训练任务失败：%s，返回码：%s", task_id, result.returncode)
    db = SessionLocal()
    try:
        failed_task = db.get(TrainTask, task_id)
        if failed_task is not None and failed_task.status == "running":
            failed_task.status = "failed"
            failed_task.finished_at = datetime.now()
            db.commit()
    finally:
        db.close()


def get_train_task(db: Session, task_id: int) -> TrainTask | None:
    return db.get(TrainTask, task_id)


def get_train_log_path(task_id: int) -> Path:
    return settings.LOG_DIR / f"train_task_{task_id}.log"
