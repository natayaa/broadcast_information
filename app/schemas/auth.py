"""Pydantic schemas for authentication and users."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=6, max_length=128)
    email: EmailStr
    firstname: str | None = Field(default=None, max_length=80)
    lastname: str | None = Field(default=None, max_length=80)
    mail_password: str | None = None
    is_admin: bool = False
