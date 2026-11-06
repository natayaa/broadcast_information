"""Domain errors mapped to HTTP responses by the application handler."""

from __future__ import annotations


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ValidationError(AppError):
    status_code = 422


class MailDeliveryError(AppError):
    status_code = 502
