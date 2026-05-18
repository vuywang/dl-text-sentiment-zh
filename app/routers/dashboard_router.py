from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import get_dashboard_charts, get_dashboard_summary
from app.utils.response import fail, success

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(get_dashboard_summary(db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=4001)


@router.get("/charts")
def dashboard_charts_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(get_dashboard_charts(db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=4002)
