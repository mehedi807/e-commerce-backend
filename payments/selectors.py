from django.db.models import QuerySet
from core.exceptions import ApplicationError
from payments.models import Payment


def payment_list_by_order(*, order_id: int) -> QuerySet[Payment]:
    return Payment.objects.filter(order_id=order_id).select_related('order', 'order__user')

def payment_get_by_id(*, payment_id: int) -> Payment:
    try:
        return Payment.objects.select_related('order', 'order__user').get(id=payment_id)
    except Payment.DoesNotExist:
        raise ApplicationError("Payment not found.", status_code=404)

def payment_get_by_transaction_id(*, transaction_id: str) -> Payment:
    try:
        return Payment.objects.select_related('order', 'order__user').get(transaction_id=transaction_id)
    except Payment.DoesNotExist:
        raise ApplicationError("Payment not found.", status_code=404)
