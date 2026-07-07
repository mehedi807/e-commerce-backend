from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.serializers import as_serializer_error
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ApplicationError(APIException):
    status_code = 400
    default_detail = 'An application error occurred.'
    default_code = 'application_error'

    def __init__(self, message: str, extra: dict | None = None, status_code: int | None = None):
        self.extra = extra or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=message)


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    response = exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, exceptions.ValidationError):
        response.data = {
            'message': 'Validation error',
            'extra': {'fields': response.data},
        }
    else:
        data = response.data
        detail = ""
        extra = getattr(exc, 'extra', {})

        if isinstance(data, dict):
            detail = data.pop('detail', '')
            for key, value in data.items():
                extra[key] = value
        else:
            detail = str(data)

        response.data = {
            'message': detail,
            'extra': extra,
        }

    return response
