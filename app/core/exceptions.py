from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.core.logging import get_logger

logger = get_logger(__name__)

class AppException(Exception):
    def __init__(self, status_code: int, detail: str, code: str = None):
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(detail)

class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=404, detail=f"{resource} not found", code="NOT_FOUND"
        )

class ForbiddenException(AppException):
    def __int__(self, detail: str = "You don't have permission to perform this action"):
        super().__init__(status_code=403, detail=detail, code="FORBIDDEN")

class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail, code="UNAUTHORIZED")

class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail, code="CONFLICT")

class BadRequestException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, code="BAD_REQUEST")

class RateLimitException(AppException):
    def __init__(self):
        super().__init__(status_code=429, detail="Too many requests. Please slow down", code="RATE_LIMIT_EXCEEDED")

def error_response(status_code: int, detail: str, code: str = None, request_id: str = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={
        "success": False,
        "error": {
            "code" : code or "ERROR",
                  "message" : detail
                  },
            "request_id": request_id
        }
    )

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            exc.detail,
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "code": exc.code,
                "path": request.url.path
            }
        )
        return error_response(exc.status_code, exc.detail, exc.code, request_id)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            str(exc.detail),
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "path": request.url.path
            }
        )
        return error_response(exc.status_code, str(exc.detail), "HTTP_ERROR", request_id)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        first_error = errors[0]
        field = " → ".join(str(loc) for loc in first_error["loc"])
        message = f"{field}: {first_error['msg']}"

        logger.warning(
            "Validation error",
            extra={
                "request_id": request_id,
                "errors": errors,
                "path": request.url.path
            }
        )
        return error_response(422, message, "VALIDATION_ERROR", request_id)

    @app.exception_handler(ExpiredSignatureError)
    async def expired_token_handler(request: Request, exc: ExpiredSignatureError):
        request_id = getattr(request.state, "request_id", None)
        return error_response(401, "Token has expired", "TOKEN_EXPIRED", request_id)

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError):
        request_id = getattr(request.state, 'request_id', None)
        return error_response(401, "Invalid token", "INVALID_TOKEN", request_id)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Database integrity error",
            extra={"request_id": request_id, "error": str(exc.orig), "path": request.url.path}
        )
        return error_response(409, "Resource already exists", "CONFLICT", request_id)

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Database operational error",
            extra={"request_id": request_id, "error": str(exec), "path": request.url.path}
        )
        return error_response(503, "Database unavailable", "DB_ERROR", request_id)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unexpected error",
            extra={"request_id": request_id, "error": str(exec), "path": request.url.path}
        )
        return error_response(500, "Internal server error", "INTERNAL_ERROR", request_id)