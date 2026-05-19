from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.history_service import (
    latest_completed_train_task,
    list_batch_tasks,
    list_train_tasks,
    recent_analysis_records,
    recent_train_tasks,
    sentiment_statistics,
    train_task_to_dict,
)
from app.services.model_service import ensure_default_model, predict_text
from app.utils.file_utils import resolve_storage_path, storage_url

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.APP_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def index_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    active_model = ensure_default_model(db)
    stats = sentiment_statistics(db)
    context = {
        "request": request,
        "project_name": settings.PROJECT_NAME,
        "active_model": active_model,
        "db_path": settings.DB_PATH,
        "db_status": "已连接" if settings.DB_PATH.exists() else "待初始化",
        "recent_train_tasks": recent_train_tasks(db, limit=5),
        "recent_analysis_records": recent_analysis_records(db, limit=5),
        "stats": stats,
    }
    return templates.TemplateResponse(request, "index.html", context)


@router.get("/predict", response_class=HTMLResponse)
def predict_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "predict.html",
        {
            "request": request,
            "recent_records": recent_analysis_records(db, limit=10),
        },
    )


@router.get("/batch", response_class=HTMLResponse)
def batch_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "batch.html",
        {
            "request": request,
            "recent_batch_tasks": list_batch_tasks(db, limit=10),
        },
    )


@router.get("/train", response_class=HTMLResponse)
def train_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "train.html",
        {
            "request": request,
            "recent_train_tasks": list_train_tasks(db, limit=10),
        },
    )


@router.get("/evaluate", response_class=HTMLResponse)
def evaluate_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    latest_task = latest_completed_train_task(db)
    latest_task_dict = train_task_to_dict(latest_task) if latest_task else None
    confusion_matrix_url = storage_url(latest_task.confusion_matrix_path) if latest_task else None
    resolved_model_dir = resolve_storage_path(latest_task.model_dir) if latest_task and latest_task.model_dir else None
    loss_curve_path = resolved_model_dir / "loss_curve.png" if resolved_model_dir else None
    loss_curve_url = storage_url(loss_curve_path) if loss_curve_path else None

    sample_texts = [
        "这家店的服务很好，菜品也很新鲜。",
        "电影节奏拖沓，剧情也很无聊。",
        "物流速度很快，包装完整。",
        "客服态度不好，问题一直没有解决。",
        "整体体验不错，下次还会购买。",
    ]
    sample_predictions: list[dict[str, object]] = []
    if latest_task is not None:
        for text in sample_texts:
            try:
                result = predict_text(text, db)
                sample_predictions.append({"text": text, **result})
            except Exception as exc:  # noqa: BLE001
                sample_predictions.append({"text": text, "error": str(exc)})

    return templates.TemplateResponse(
        request,
        "evaluate.html",
        {
            "request": request,
            "latest_task": latest_task_dict,
            "confusion_matrix_url": confusion_matrix_url,
            "loss_curve_url": loss_curve_url,
            "sample_predictions": sample_predictions,
        },
    )


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "request": request,
            "analysis_records": recent_analysis_records(db, limit=100),
            "batch_tasks": list_batch_tasks(db, limit=100),
            "train_tasks": list_train_tasks(db, limit=100),
        },
    )
