from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.history_service import list_analysis_records, list_batch_tasks, list_train_tasks
from app.utils.response import success

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/analysis")
def history_analysis_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_analysis_records(db, limit=200))


@router.get("/batch")
def history_batch_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_batch_tasks(db, limit=200))


@router.get("/train")
def history_train_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_train_tasks(db, limit=200))
