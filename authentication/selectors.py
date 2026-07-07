from authentication.models import User
from core.exceptions import ApplicationError


def user_get_by_id(*, user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ApplicationError('User not found.', status_code=404)


def user_get_login_data(*, user: User) -> dict:
    return {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'created_at': user.created_at,
    }
