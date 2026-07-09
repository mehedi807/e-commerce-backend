from django.db.models import QuerySet

from authentication.models import User
from core.exceptions import ApplicationError
from orders.models import Order


def order_list(*, user: User) -> QuerySet[Order]:
    return (
        Order.objects
        .filter(user=user)
        .select_related('user')
        .prefetch_related('items__product')
    )


def order_get_by_id(*, order_id: int, user: User | None = None) -> Order:
    try:
        qs = Order.objects.select_related('user').prefetch_related('items__product')
        if user is not None and not user.is_staff:
            order = qs.get(id=order_id, user=user)
        else:
            order = qs.get(id=order_id)
        return order
    except Order.DoesNotExist:
        raise ApplicationError('Order not found.', status_code=404)


def order_list_admin() -> QuerySet[Order]:
    return (
        Order.objects
        .select_related('user')
        .prefetch_related('items__product')
    )
