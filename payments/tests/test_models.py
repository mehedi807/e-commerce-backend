from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from orders.models import Order
from payments import constants
from payments.models import Payment

User = get_user_model()


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test.customer@shop.com',
            password='P@ssw0rd123!',
            first_name='Test',
            last_name='Customer',
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
        )

    def test_payment_creation_success(self):
        payment = Payment.objects.create(
            order=self.order,
            provider=constants.PaymentProvider.STRIPE,
            transaction_id='pi_mock_123',
            status=constants.PaymentStatus.PENDING,
            raw_response={"id": "pi_mock_123"},
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.provider, constants.PaymentProvider.STRIPE)
        self.assertEqual(payment.transaction_id, 'pi_mock_123')
        self.assertEqual(payment.status, constants.PaymentStatus.PENDING)
        self.assertEqual(payment.raw_response, {"id": "pi_mock_123"})
        self.assertIsNotNone(payment.created_at)
        self.assertEqual(
            str(payment),
            f"Payment #{payment.id} - Order #{self.order.id} - stripe - pending"
        )

    def test_payment_transaction_id_unique(self):
        Payment.objects.create(
            order=self.order,
            provider=constants.PaymentProvider.STRIPE,
            transaction_id='pi_unique_123',
            status=constants.PaymentStatus.PENDING,
        )
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                order=self.order,
                provider=constants.PaymentProvider.BKASH,
                transaction_id='pi_unique_123',
                status=constants.PaymentStatus.PENDING,
            )
