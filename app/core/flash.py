"""Tiny session-backed flash messages."""

from __future__ import annotations

from typing import Literal

from fastapi import Request

Category = Literal["success", "danger", "warning", "info"]


def flash(request: Request, message: str, category: Category = "info") -> None:
    request.session.setdefault("_flashes", []).append({"message": message, "category": category})


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return request.session.pop("_flashes", [])
