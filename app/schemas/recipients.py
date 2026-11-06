"""Pydantic schemas for recipients."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.services.catalog import DIVISIONS

RecipientCategory = Literal["Direct", "CC"]


class RecipientCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    division: str = Field(min_length=1, max_length=120)
    category: RecipientCategory = "Direct"

    @field_validator("category", mode="before")
    @classmethod
    def _normalise_category(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if value.lower() == "cc":
                return "CC"
            if value.lower() == "direct":
                return "Direct"
        return value

    @field_validator("division")
    @classmethod
    def _known_division(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in DIVISIONS:
            raise ValueError(f"Unknown division '{cleaned}'")
        return cleaned


class RecipientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None = None
    name: str | None = None
    division: str | None = None
    category: str | None = None
    created_at: datetime | None = None


class RecipientPage(BaseModel):
    items: list[RecipientOut]
    total: int
    page: int
    page_size: int
    pages: int
