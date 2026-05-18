from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.insight_service import generate_error_samples, list_low_confidence_records
from app.utils.response import fail, success

router = APIRouter(prefix="/api", tags=["insights"])


@router.get("/review/low-confidence")
def low_confidence_api(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return success(list_low_confidence_records(db, limit=limit))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=7001)


@router.get("/error-samples")
def error_samples_api(
    limit: int = Query(20, ge=1, le=100),
    scan_limit: int = Query(200, ge=20, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return success(generate_error_samples(db, limit=limit, scan_limit=scan_limit))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=7002)
