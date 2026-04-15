from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schema.train_schema import TrainStartRequest
from app.services.history_service import train_task_to_dict
from app.services.train_service import get_train_task, start_training_task
from app.utils.response import fail, success

router = APIRouter(prefix="/api/train", tags=["train"])


@router.post("/start")
def train_start_api(
    payload: TrainStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return success(start_training_task(payload, db, background_tasks))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=3001)


@router.get("/{task_id}")
def train_detail_api(task_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    task = get_train_task(db, task_id)
    if task is None:
        return fail("训练任务不存在", code=3002)
    return success(train_task_to_dict(task))
