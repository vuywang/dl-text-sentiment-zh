from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.batch_service import get_batch_detail, get_batch_task, process_batch_upload
from app.utils.response import fail, success

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/upload")
def batch_upload_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return success(process_batch_upload(file, db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=2001)


@router.get("/{task_id}")
def batch_detail_api(task_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(get_batch_detail(db, task_id))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=2002)


@router.get("/{task_id}/download")
def batch_download_api(task_id: int, db: Session = Depends(get_db)):
    task = get_batch_task(db, task_id)
    if task is None or not task.result_file_path:
        return fail("批量任务结果不存在", code=2003)
    result_path = Path(task.result_file_path)
    if not result_path.exists():
        return fail("导出文件不存在", code=2004)
    return FileResponse(
        path=result_path,
        filename=result_path.name,
        media_type="text/csv",
    )
