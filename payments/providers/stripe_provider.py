import stripe
from django.conf import settings
from django.db import transaction
from core.exceptions import ApplicationError
from orders.models import Order
from orders.services import order_mark_paid
from payments import constants
from payments.models import Payment

class StripePaymentProvider:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def initiate_payment(self, *, order: Order) -> dict:
        try:
            unit_amount = int(order.total_amount * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=order.user.email,
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': unit_amount,
                            'product_data': {
                                'name': f"Order #{order.id} Payment",
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={
                    'order_id': str(order.id)
                }
            )
        except Exception as e:
            raise ApplicationError(f"Stripe Checkout Session creation failed: {str(e)}")

        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                provider=constants.PaymentProvider.STRIPE,
                transaction_id=session.id,
                status=constants.PaymentStatus.PENDING,
                raw_response=session.to_dict(),
            )

        return {
            'payment_id': payment.id,
            'transaction_id': session.id,
            'checkout_url': session.url,
        }

    def handle_webhook(self, *, payload: bytes, headers: dict) -> dict:
        sig_header = headers.get('stripe-signature')
        if not sig_header:
            raise ApplicationError("Missing stripe-signature header", status_code=400)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise ApplicationError(f"Invalid payload: {str(e)}", status_code=400)
        except stripe.error.SignatureVerificationError as e:
            raise ApplicationError(f"Invalid signature: {str(e)}", status_code=400)

        event_dict = event.to_dict()
        event_type = event_dict.get('type')
        data_object = event_dict.get('data', {}).get('object', {})

        event_handlers = {
            'checkout.session.completed': self._handle_checkout_session_completed,
            'checkout.session.async_payment_succeeded': self._handle_async_payment_succeeded,
            'checkout.session.async_payment_failed': self._handle_async_payment_failed,
            'checkout.session.expired': self._handle_checkout_session_expired,
        }

        handler = event_handlers.get(event_type)

        if handler:
            return handler(data_object)

        return {'status': 'ignored', 'event_type': event_type}

    def _handle_checkout_session_completed(self, session: dict) -> dict:
        if session.get('payment_status') == 'paid':
            return self._fulfill_payment(session)
        return {'status': 'ignored', 'reason': 'Payment status is not paid'}

    def _handle_async_payment_succeeded(self, session: dict) -> dict:
        return self._fulfill_payment(session)

    def _handle_async_payment_failed(self, session: dict) -> dict:
        return self._fail_payment(session)

    def _handle_checkout_session_expired(self, session: dict) -> dict:
        return self._fail_payment(session)

    def _fulfill_payment(self, session: dict) -> dict:
        order_id = session.get('metadata', {}).get('order_id')
        transaction_id = session.get('id')

        if not order_id or not transaction_id:
            return {'status': 'ignored', 'reason': 'Missing metadata.order_id or session id'}

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(transaction_id=transaction_id)
                if payment.status != constants.PaymentStatus.SUCCESS:
                    payment.status = constants.PaymentStatus.SUCCESS
                    payment.raw_response = {**payment.raw_response, 'webhook_payload': session}
                    payment.save(update_fields=['status', 'raw_response', 'updated_at'])
                    order_mark_paid(order=payment.order)
            except Payment.DoesNotExist:
                payment = Payment.objects.select_for_update().filter(order_id=order_id).first()
                if payment and payment.status != constants.PaymentStatus.SUCCESS:
                    payment.status = constants.PaymentStatus.SUCCESS
                    payment.raw_response = {**payment.raw_response, 'webhook_payload': session}
                    payment.save(update_fields=['status', 'raw_response', 'updated_at'])
                    order_mark_paid(order=payment.order)

        return {'status': 'processed', 'transaction_id': transaction_id, 'payment_status': 'success'}

    def _fail_payment(self, session: dict) -> dict:
        transaction_id = session.get('id')

        if not transaction_id:
            return {'status': 'ignored', 'reason': 'Missing session id'}

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(transaction_id=transaction_id)
                if payment.status != constants.PaymentStatus.SUCCESS:
                    payment.status = constants.PaymentStatus.FAILED
                    payment.raw_response = {**payment.raw_response, 'webhook_payload': session}
                    payment.save(update_fields=['status', 'raw_response', 'updated_at'])
            except Payment.DoesNotExist:
                pass

        return {'status': 'processed', 'transaction_id': transaction_id, 'payment_status': 'failed'}
