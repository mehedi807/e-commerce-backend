from django.db import IntegrityError, transaction

from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import User
from core.exceptions import ApplicationError


def user_create(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> User:
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
    except IntegrityError:
        raise ApplicationError('A user with this email already exists.', status_code=400)

    return user


def user_get_tokens(*, user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
