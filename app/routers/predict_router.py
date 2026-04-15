from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schema.predict_schema import PredictRequest
from app.services.predict_service import predict_and_save
from app.utils.response import fail, success

router = APIRouter(prefix="/api", tags=["predict"])


@router.post("/predict")
def predict_api(payload: PredictRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(predict_and_save(payload.text, db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=1001)
