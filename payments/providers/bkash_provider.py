import requests
from django.conf import settings
from django.db import transaction
from core.exceptions import ApplicationError
from orders.models import Order
from orders.services import order_mark_paid
from payments import constants
from payments.models import Payment


class BkashPaymentProvider:
    def __init__(self):
        self.base_url = settings.BKASH_BASE_URL.rstrip('/')
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD

    def _grant_token(self) -> str:
        url = f"{self.base_url}/checkout/token/grant"
        headers = {
            "username": self.username,
            "password": self.password,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_json = response.json()
        except Exception as e:
            raise ApplicationError(f"bKash token grant request failed: {str(e)}")

        if 'id_token' not in response_json:
            error_msg = response_json.get('statusMessage') or response_json.get('errorMessage') or "Unknown error"
            raise ApplicationError(f"bKash auth failed: {error_msg}")

        return response_json['id_token']

    def _get_headers(self) -> dict:
        id_token = self._grant_token()
        return {
            "Authorization": id_token,
            "X-APP-Key": self.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def initiate_payment(self, *, order: Order) -> dict:
        url = f"{self.base_url}/checkout/payment/create"
        payload = {
            "amount": f"{order.total_amount:.2f}",
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"ORDER-{order.id}"
        }

        try:
            headers = self._get_headers()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_json = response.json()
        except Exception as e:
            raise ApplicationError(f"bKash payment creation failed: {str(e)}")

        payment_id = response_json.get('paymentID')

        if not payment_id:
            error_msg = response_json.get('statusMessage') or response_json.get('errorMessage') or "Unknown error"
            raise ApplicationError(f"bKash payment initiation failed: {error_msg}")

        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                provider=constants.PaymentProvider.BKASH,
                transaction_id=payment_id,
                status=constants.PaymentStatus.PENDING,
                raw_response=response_json,
            )

        return {
            'transaction_id': payment_id,
            'payment_id': payment.id,
        }

    def execute_payment(self, *, payment_id: str) -> str:
        url = f"{self.base_url}/checkout/payment/execute/{payment_id}"

        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, timeout=30)
            response_json = response.json()
        except Exception as e:
            raise ApplicationError(f"bKash payment execution failed: {str(e)}")

        transaction_status = response_json.get('transactionStatus')
        error_code = response_json.get('errorCode')

        new_status = constants.PaymentStatus.PENDING

        if transaction_status == "Completed":
            new_status = constants.PaymentStatus.SUCCESS
        elif error_code or transaction_status in ["Failed", "Cancelled"]:
            new_status = constants.PaymentStatus.FAILED

        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(transaction_id=payment_id)
            payment.status = new_status
            payment.raw_response = response_json
            payment.save(update_fields=['status', 'raw_response', 'updated_at'])

            if new_status == constants.PaymentStatus.SUCCESS:
                order_mark_paid(order=payment.order)

        return new_status

    def query_payment(self, *, payment_id: str) -> dict:
        url = f"{self.base_url}/checkout/payment/query/{payment_id}"

        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            response_json = response.json()
        except Exception as e:
            raise ApplicationError(f"bKash payment query failed: {str(e)}")

        transaction_status = response_json.get('transactionStatus')
        error_code = response_json.get('errorCode')

        new_status = constants.PaymentStatus.PENDING
        if transaction_status == "Completed":
            new_status = constants.PaymentStatus.SUCCESS
        elif error_code or transaction_status in ["Failed", "Cancelled"]:
            new_status = constants.PaymentStatus.FAILED

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(transaction_id=payment_id)
                payment.status = new_status
                payment.raw_response = response_json
                payment.save(update_fields=['status', 'raw_response', 'updated_at'])

                if new_status == constants.PaymentStatus.SUCCESS:
                    order_mark_paid(order=payment.order)
            except Payment.DoesNotExist:
                pass

        return response_json


    def handle_webhook(self, *, payload: bytes, headers: dict) -> dict:
        import json
        message_type = headers.get('HTTP_X_AMZ_SNS_MESSAGE_TYPE') or headers.get('x-amz-sns-message-type')

        try:
            data = json.loads(payload.decode('utf-8'))
        except Exception as e:
            raise ApplicationError(f"Invalid webhook payload: {str(e)}", status_code=400)

        if message_type == 'SubscriptionConfirmation':
            subscribe_url = data.get('SubscribeURL')
            if subscribe_url:
                try:
                    requests.get(subscribe_url, timeout=15)
                    return {'status': 'subscribed', 'message_type': message_type}
                except Exception as e:
                    raise ApplicationError(f"Subscription confirmation request failed: {str(e)}", status_code=400)
            raise ApplicationError("Missing SubscribeURL in SubscriptionConfirmation", status_code=400)

        elif message_type == 'Notification':
            message_str = data.get('Message')
            if not message_str:
                raise ApplicationError("Missing Message field in webhook payload", status_code=400)

            try:
                message_json = json.loads(message_str) if isinstance(message_str, str) else message_str
            except Exception as e:
                raise ApplicationError(f"Invalid notification message JSON: {str(e)}", status_code=400)

            invoice_num = message_json.get('merchantInvoiceNumber')
            transaction_status = message_json.get('transactionStatus')

            if not invoice_num or not invoice_num.startswith('ORDER-'):
                return {'status': 'ignored', 'reason': f'Invalid invoice number format: {invoice_num}'}

            order_id = invoice_num.replace('ORDER-', '')

            with transaction.atomic():
                try:
                    payment = Payment.objects.select_for_update().filter(order_id=order_id).first()
                    if not payment:
                        return {'status': 'ignored', 'reason': f'No payment record found for order {order_id}'}

                    new_status = constants.PaymentStatus.PENDING
                    if transaction_status == "Completed":
                        new_status = constants.PaymentStatus.SUCCESS
                    elif transaction_status in ["Failed", "Cancelled"]:
                        new_status = constants.PaymentStatus.FAILED

                    if payment.status != constants.PaymentStatus.SUCCESS:
                        payment.status = new_status
                        payment.raw_response = {**payment.raw_response, 'webhook_payload': message_json}
                        payment.save(update_fields=['status', 'raw_response', 'updated_at'])
                        if new_status == constants.PaymentStatus.SUCCESS:
                            order_mark_paid(order=payment.order)
                except Exception as e:
                    raise ApplicationError(f"Database update failed: {str(e)}", status_code=500)

            return {'status': 'processed', 'payment_id': payment.transaction_id, 'payment_status': new_status}

        return {'status': 'ignored', 'message_type': message_type}