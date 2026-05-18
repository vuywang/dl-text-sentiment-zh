from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluate_service import get_latest_evaluation
from app.utils.response import fail, success

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])


@router.get("/latest")
def evaluate_latest_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(get_latest_evaluation(db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=5001)
