from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluate_service import list_model_comparison
from app.services.model_service import activate_model
from app.utils.response import fail, success

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def model_list_api(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return success(list_model_comparison(db))
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=6001)


@router.post("/{model_id}/activate")
def model_activate_api(model_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        model = activate_model(db, model_id)
        return success(model, message="模型已启用")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), code=6002)
