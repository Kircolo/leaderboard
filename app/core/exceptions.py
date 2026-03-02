class AppError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class DependencyUnavailableError(AppError):
    status_code = 503
    code = "dependency_unavailable"

