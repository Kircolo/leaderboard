from dataclasses import asdict, dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


@dataclass(slots=True)
class ErrorPayload:
    code: str
    message: str


async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    payload = ErrorPayload(exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"error": asdict(payload)})


async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    payload = ErrorPayload("internal_server_error", "An unexpected error occurred.")
    return JSONResponse(
        status_code=500,
        content={"error": asdict(payload)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
