class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

class ResourceNotFound(AppException):
    def __init__(self, message: str):
        super().__init__(404, message)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(409, message)

class ForbiddenException(AppException):
    def __init__(self, message: str):
        super().__init__(403, message)

class BadRequestException(AppException):
    def __init__(self, message: str):
        super().__init__(400, message)