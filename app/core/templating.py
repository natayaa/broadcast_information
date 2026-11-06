"""Template rendering helpers shared by every HTML route."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR, settings
from app.core.flash import pop_flashes

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def format_datetime(value: Any, fmt: str = "%d %b %Y, %H:%M") -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)


templates.env.filters["datetime"] = format_datetime
templates.env.globals["app_name"] = settings.app_name


def render(
    request: Request,
    template_name: str,
    *,
    user: Any = None,
    status_code: int = 200,
    **context: Any,
) -> Any:
    context.setdefault("current_user", user)
    context.setdefault("flashes", pop_flashes(request))
    context.setdefault("active_page", "")
    return templates.TemplateResponse(request, template_name, context, status_code=status_code)
