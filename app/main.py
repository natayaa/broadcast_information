"""FastAPI application factory and global error handling."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app import __version__
from app.config import STATIC_DIR, settings
from app.core.errors import AppError
from app.core.templating import render
from app.db.base import init_db
from app.routers import auth, broadcast, documents, pages, recipients

logger = logging.getLogger("broadcast")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def _wants_json(request: Request) -> bool:
    if request.url.path.startswith("/api"):
        return True
    accept = request.headers.get("accept", "")
    return "application/json" in accept and "text/html" not in accept


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    logger.info("%s v%s started", settings.app_name, __version__)
    yield
    logger.info("%s stopped", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="TV Engineering document broadcast system",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=settings.cookie_https_only,
    )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(auth.auth)
    app.include_router(pages.pages)
    app.include_router(documents.documents)
    app.include_router(recipients.recipients)
    app.include_router(broadcast.broadcast)

    _register_error_handlers(app)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        if not request.url.path.startswith("/static"):
            logging.getLogger("access").info(
                "%s %s -> %s (%.1f ms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )
        return response

    return app


def _error_page(request: Request, status_code: int, message: str):
    user = None
    try:
        from app.core.deps import get_optional_user
        from app.db.base import SessionLocal

        with SessionLocal() as db:
            user = get_optional_user(request, db)
    except Exception:  # never let error-page rendering mask the original error
        logger.exception("Could not resolve the current user for the error page")

    return render(
        request,
        "error.html",
        user=user,
        status_code=status_code,
        page_title=f"Error {status_code}",
        status_code_value=status_code,
        message=message,
    )


def _register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        if _wants_json(request):
            return JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        return _error_page(request, exc.status_code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        if exc.status_code == status.HTTP_401_UNAUTHORIZED and not _wants_json(request):
            target = request.url.path
            if request.url.query:
                target = f"{target}?{request.url.query}"
            return RedirectResponse(f"/login?next={quote(target, safe='')}", status_code=status.HTTP_303_SEE_OTHER)

        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        if _wants_json(request):
            return JSONResponse(
                {"detail": detail},
                status_code=exc.status_code,
                headers=getattr(exc, "headers", None),
            )
        return _error_page(request, exc.status_code, detail)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        if _wants_json(request):
            errors = [
                {
                    "loc": list(error.get("loc", [])),
                    "msg": error.get("msg", "Invalid value"),
                    "type": error.get("type", "value_error"),
                }
                for error in exc.errors()
            ]
            return JSONResponse({"detail": errors}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
        return _error_page(request, status.HTTP_422_UNPROCESSABLE_CONTENT, "The submitted data is not valid")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        if _wants_json(request):
            return JSONResponse({"detail": "Internal server error"}, status_code=500)
        return _error_page(request, 500, "An unexpected error occurred. Please try again.")


app = create_app()
