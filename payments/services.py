from django.db import transaction
from core.exceptions import ApplicationError
from orders.models import Order
from payments import constants
from payments.models import Payment
from payments.providers.base import PaymentProvider as BasePaymentProvider


def get_provider(provider_name: str) -> BasePaymentProvider:
    prov = provider_name.lower()
    if prov == constants.PaymentProvider.STRIPE:
        from payments.providers.stripe_provider import StripePaymentProvider
        return StripePaymentProvider()
    elif prov == constants.PaymentProvider.BKASH:
        from payments.providers.bkash_provider import BkashPaymentProvider
        return BkashPaymentProvider()
    else:
        raise ApplicationError(f"Unsupported payment provider: {provider_name}", status_code=400)


def payment_initiate(*, order: Order, provider: str) -> dict:
    if order.status != 'pending':
        raise ApplicationError(f"Cannot initiate payment for an order in {order.status} status.")

    if Payment.objects.filter(order=order, status=constants.PaymentStatus.SUCCESS).exists():
        raise ApplicationError("This order is already successfully paid.")

    prov = get_provider(provider)
    return prov.initiate_payment(order=order)


def payment_confirm_stripe(*, transaction_id: str) -> Payment:
    try:
        payment = Payment.objects.get(transaction_id=transaction_id, provider=constants.PaymentProvider.STRIPE)
    except Payment.DoesNotExist:
        raise ApplicationError("Payment record not found.", status_code=404)

    prov = get_provider(constants.PaymentProvider.STRIPE)
    prov.confirm_payment(transaction_id=transaction_id)
    payment.refresh_from_db()
    return payment


def payment_execute_bkash(*, payment_id: str) -> Payment:
    try:
        payment = Payment.objects.get(transaction_id=payment_id, provider=constants.PaymentProvider.BKASH)
    except Payment.DoesNotExist:
        raise ApplicationError("Payment record not found.", status_code=404)

    prov = get_provider(constants.PaymentProvider.BKASH)
    prov.execute_payment(payment_id=payment_id)
    payment.refresh_from_db()
    return payment


def payment_query_bkash(*, payment_id: str) -> dict:
    prov = get_provider(constants.PaymentProvider.BKASH)
    return prov.query_payment(payment_id=payment_id)


def payment_handle_stripe_webhook(*, payload: bytes, sig_header: str) -> dict:
    prov = get_provider(constants.PaymentProvider.STRIPE)
    return prov.handle_webhook(payload=payload, headers={'stripe-signature': sig_header})


def payment_handle_bkash_callback(*, payment_id: str, status: str) -> dict:
    try:
        payment = Payment.objects.get(transaction_id=payment_id, provider=constants.PaymentProvider.BKASH)
    except Payment.DoesNotExist:
        raise ApplicationError("Payment record not found.", status_code=404)

    prov = get_provider(constants.PaymentProvider.BKASH)
    return prov.handle_callback(payment_id=payment_id, status=status)


def payment_handle_bkash_webhook(*, payload: bytes, headers: dict) -> dict:
    prov = get_provider(constants.PaymentProvider.BKASH)
    return prov.handle_webhook(payload=payload, headers=headers)
