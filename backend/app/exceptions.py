from urllib.request import Request
from starlette.responses import JSONResponse
from main import app


class BaseException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


@app.exception_handler(BaseException)
async def app_exception_handler(request: Request, exc: BaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


class ResourceNotFound(BaseException):
    def __init__(self, message: str):
        super().__init__(404, message)


class ConflictException(BaseException):
    def __init__(self, message: str):
        super().__init__(409, message)


class ForbiddenException(BaseException):
    def __init__(self, message: str):
        super().__init__(403, message)


class BadRequestException(BaseException):
    def __init__(self, message: str):
        super().__init__(400, message)