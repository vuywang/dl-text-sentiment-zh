from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.history_service import (
    clear_analysis_records,
    clear_batch_tasks,
    delete_analysis_records,
    delete_batch_tasks,
    list_analysis_records,
    list_batch_tasks,
    list_train_tasks,
)
from app.utils.response import fail, success

router = APIRouter(prefix="/api/history", tags=["history"])


class DeleteIdsRequest(BaseModel):
    ids: list[int] = Field(default_factory=list)


@router.get("/analysis")
def history_analysis_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_analysis_records(db, limit=200))


@router.get("/batch")
def history_batch_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_batch_tasks(db, limit=200))


@router.get("/train")
def history_train_api(db: Session = Depends(get_db)) -> dict[str, object]:
    return success(list_train_tasks(db, limit=200))


@router.post("/analysis/delete")
def delete_history_analysis_api(
    payload: DeleteIdsRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        deleted_count = delete_analysis_records(db, payload.ids)
        return success({"deleted_count": deleted_count}, message="已删除选中的单文本记录")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=3001)


@router.post("/analysis/clear")
def clear_history_analysis_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        deleted_count = clear_analysis_records(db)
        return success({"deleted_count": deleted_count}, message="已清空单文本记录")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=3002)


@router.post("/batch/delete")
def delete_history_batch_api(
    payload: DeleteIdsRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        result = delete_batch_tasks(db, payload.ids)
        return success(result, message="已删除选中的批量任务")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=3003)


@router.post("/batch/clear")
def clear_history_batch_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        result = clear_batch_tasks(db)
        return success(result, message="已清空批量任务")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=3004)
