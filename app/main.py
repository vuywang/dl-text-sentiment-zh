from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import ensure_directories, settings
from app.core.database import SessionLocal, init_db
from app.core.logger import get_logger
from app.routers import batch_router, history_router, page_router, predict_router, train_router
from app.services.model_service import ensure_default_model, load_active_model_safely
from app.utils.response import fail

logger = get_logger(__name__)
templates = Jinja2Templates(directory=str(settings.APP_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    init_db()
    db = SessionLocal()
    try:
        ensure_default_model(db)
    finally:
        db.close()
    load_active_model_safely()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

app.include_router(page_router.router)
app.include_router(predict_router.router)
app.include_router(batch_router.router)
app.include_router(train_router.router)
app.include_router(history_router.router)


def _is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api/")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if _is_api_request(request):
        return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail), code=exc.status_code))
    return templates.TemplateResponse(
        request,
        "error.html",
        {"request": request, "message": str(exc.detail)},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "请求参数校验失败"
    if _is_api_request(request):
        return JSONResponse(status_code=422, content=fail(message, code=422))
    return templates.TemplateResponse(
        request,
        "error.html",
        {"request": request, "message": message},
        status_code=422,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常：%s", exc)
    if _is_api_request(request):
        return JSONResponse(status_code=500, content=fail("系统内部错误", code=500))
    return templates.TemplateResponse(
        request,
        "error.html",
        {"request": request, "message": "系统处理请求时出现异常，请查看日志文件。"},
        status_code=500,
    )
