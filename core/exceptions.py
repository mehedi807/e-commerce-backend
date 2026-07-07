from rest_framework.views import exception_handler
from rest_framework import exceptions
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response


class ApplicationError(Exception):
    def __init__(self, message, extra=None, status_code=400):
        super().__init__(message)
        self.message = message
        self.extra = extra or {}
        self.status_code = status_code


def api_exception_handler(exc, context):
    
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, ApplicationError):
            data = {"message": exc.message, "extra": exc.extra}
            return Response(data, status=exc.status_code)

        return response

    if isinstance(exc.detail, (list, dict)):
        response.data = {"message": "Validation error", "extra": {"fields": response.data}}
    else:
        detail_msg = response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data
        response.data = {"message": detail_msg}

    return response


def as_serializer_error(exc):
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    if hasattr(exc, "message"):
        return exc.message
    return str(exc)
