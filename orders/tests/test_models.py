from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.exceptions import ApplicationError
from orders.constants import OrderStatus
from orders.models import Order, OrderItem
from orders import services
from products.models import Category, Product
from products.constants import ProductStatus

User = get_user_model()


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='alice.vance@shop.com',
            password='P@ssw0rd123!',
            first_name='Alice',
            last_name='Vance',
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
        )
        self.product = Product.objects.create(
            name='iPhone 16',
            sku='PHONE-IP16',
            price=Decimal('999.99'),
            stock=10,
            status=ProductStatus.ACTIVE,
            category=self.category,
        )

    def test_create_order_success(self):
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, Decimal('999.99'))
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertIsNotNone(order.created_at)

    def test_create_order_item_success(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('999.99'))
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
            subtotal=self.product.price,
        )
        self.assertEqual(item.order, order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.price, Decimal('999.99'))
        self.assertEqual(item.subtotal, Decimal('999.99'))

    def test_order_str_representation(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('999.99'))
        self.assertEqual(str(order), f'Order #{order.id} - alice.vance@shop.com - pending')

    def test_order_item_str_representation(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('999.99'))
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.price,
            subtotal=self.product.price * 2,
        )
        self.assertEqual(str(item), f'Item iPhone 16 (x2) for Order #{order.id}')

    def test_cascade_delete_order_deletes_items(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('999.99'))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
            subtotal=self.product.price,
        )
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        order_id = order.id
        order.delete()
        self.assertEqual(OrderItem.objects.filter(order_id=order_id).count(), 0)

    def test_product_deletion_protected_by_order_items(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('999.99'))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
            subtotal=self.product.price,
        )
        with self.assertRaises(models.ProtectedError):
            self.product.delete()


class OrderServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='alice.vance@shop.com',
            password='P@ssw0rd123!',
            first_name='Alice',
            last_name='Vance',
        )
        self.other_customer = User.objects.create_user(
            email='shop.customer@shop.com',
            password='CustomerPass123!',
            first_name='Shop',
            last_name='Customer',
        )
        self.admin = User.objects.create_superuser(
            email='admin.security@shop.com',
            password='AdminSecurePass199!',
            first_name='Admin',
            last_name='Manager',
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
        )
        self.product1 = Product.objects.create(
            name='iPhone 16',
            sku='PHONE-IP16',
            price=Decimal('999.99'),
            stock=10,
            status=ProductStatus.ACTIVE,
            category=self.category,
        )
        self.product2 = Product.objects.create(
            name='Sony WH-1000XM5',
            sku='HEAD-XM5',
            price=Decimal('349.99'),
            stock=5,
            status=ProductStatus.ACTIVE,
            category=self.category,
        )
        self.inactive_product = Product.objects.create(
            name='Discontinued Widget',
            sku='MISC-DW01',
            price=Decimal('9.99'),
            stock=100,
            status=ProductStatus.INACTIVE,
            category=self.category,
        )

    def test_order_create_success(self):
        items = [
            {'product_id': self.product1.id, 'quantity': 2},
            {'product_id': self.product2.id, 'quantity': 1},
        ]
        order = services.order_create(user=self.customer, items=items)

        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.total_amount, Decimal('2349.97'))
        self.assertEqual(order.items.count(), 2)

        item1 = order.items.get(product=self.product1)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item1.price, Decimal('999.99'))
        self.assertEqual(item1.subtotal, Decimal('1999.98'))

        item2 = order.items.get(product=self.product2)
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(item2.price, Decimal('349.99'))
        self.assertEqual(item2.subtotal, Decimal('349.99'))

    def test_order_create_empty_items_raises(self):
        with self.assertRaisesMessage(ApplicationError, 'Order must contain at least one item.'):
            services.order_create(user=self.customer, items=[])

    def test_order_create_nonexistent_product_raises(self):
        items = [{'product_id': 9999, 'quantity': 1}]
        with self.assertRaisesMessage(ApplicationError, 'Product with ID 9999 does not exist.'):
            services.order_create(user=self.customer, items=items)

    def test_order_create_inactive_product_raises(self):
        items = [{'product_id': self.inactive_product.id, 'quantity': 1}]
        with self.assertRaisesMessage(ApplicationError, f'Product {self.inactive_product.name} is not active.'):
            services.order_create(user=self.customer, items=items)

    def test_order_create_insufficient_stock_raises(self):
        items = [{'product_id': self.product1.id, 'quantity': 11}]
        with self.assertRaisesMessage(ApplicationError, 'Insufficient stock for product iPhone 16.'):
            services.order_create(user=self.customer, items=items)

    def test_order_cancel_by_owner_success(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_cancel(order=order, user=self.customer)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELED)

    def test_order_cancel_by_admin_success(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_cancel(order=order, user=self.admin)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELED)

    def test_order_cancel_by_non_owner_raises(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        with self.assertRaisesMessage(ApplicationError, 'You do not have permission to cancel this order.'):
            services.order_cancel(order=order, user=self.other_customer)

    def test_order_cancel_non_pending_raises(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_mark_paid(order=order)
        with self.assertRaisesMessage(ApplicationError, 'Cannot cancel an order that is already in paid status.'):
            services.order_cancel(order=order, user=self.customer)

    def test_order_mark_paid_reduces_stock(self):
        order = services.order_create(
            user=self.customer,
            items=[
                {'product_id': self.product1.id, 'quantity': 2},
                {'product_id': self.product2.id, 'quantity': 1},
            ],
        )
        self.assertEqual(self.product1.stock, 10)
        self.assertEqual(self.product2.stock, 5)

        services.order_mark_paid(order=order)
        order.refresh_from_db()
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()

        self.assertEqual(order.status, OrderStatus.PAID)
        self.assertEqual(self.product1.stock, 8)
        self.assertEqual(self.product2.stock, 4)

    def test_order_mark_paid_insufficient_stock_at_payment_time_raises(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 6}],
        )
        self.product1.stock = 5
        self.product1.save()

        with self.assertRaisesMessage(ApplicationError, 'Insufficient stock for product iPhone 16 during payment processing.'):
            services.order_mark_paid(order=order)

    def test_admin_update_status_pending_to_paid(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_admin_update_status(order=order, status=OrderStatus.PAID)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PAID)

    def test_admin_update_status_pending_to_canceled(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_admin_update_status(order=order, status=OrderStatus.CANCELED)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELED)

    def test_admin_update_status_invalid_transition_raises(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 1}],
        )
        services.order_cancel(order=order, user=self.admin)

        with self.assertRaisesMessage(ApplicationError, 'Cannot transition from CANCELED state.'):
            services.order_admin_update_status(order=order, status=OrderStatus.PAID)

    def test_cancel_paid_order_restores_stock(self):
        order = services.order_create(
            user=self.customer,
            items=[{'product_id': self.product1.id, 'quantity': 3}],
        )
        services.order_admin_update_status(order=order, status=OrderStatus.PAID)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 7)

        services.order_admin_update_status(order=order, status=OrderStatus.CANCELED)
        order.refresh_from_db()
        self.product1.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELED)
        self.assertEqual(self.product1.stock, 10)

    def test_order_create_duplicate_items_aggregation(self):
        items = [
            {'product_id': self.product1.id, 'quantity': 6},
            {'product_id': self.product1.id, 'quantity': 5},
        ]
        with self.assertRaisesMessage(ApplicationError, 'Insufficient stock for product iPhone 16.'):
            services.order_create(user=self.customer, items=items)

        items_ok = [
            {'product_id': self.product1.id, 'quantity': 4},
            {'product_id': self.product1.id, 'quantity': 4},
        ]
        order = services.order_create(user=self.customer, items=items_ok)
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.quantity, 8)



class OrderApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='alice.vance@shop.com',
            password='P@ssw0rd123!',
            first_name='Alice',
            last_name='Vance',
        )
        self.other_customer = User.objects.create_user(
            email='shop.customer@shop.com',
            password='CustomerPass123!',
            first_name='Shop',
            last_name='Customer',
        )
        self.admin = User.objects.create_superuser(
            email='admin.security@shop.com',
            password='AdminSecurePass199!',
            first_name='Admin',
            last_name='Manager',
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
        )
        self.product = Product.objects.create(
            name='iPhone 16',
            sku='PHONE-IP16',
            price=Decimal('1000.00'),
            stock=5,
            status=ProductStatus.ACTIVE,
            category=self.category,
        )

        self.create_url = reverse('orders:order-create')
        self.list_url = reverse('orders:order-list')
        self.admin_list_url = reverse('orders-admin:admin-order-list')

    def test_create_order_unauthenticated_raises_401(self):
        response = self.client.post(self.create_url, data={'items': []})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_authenticated_success(self):
        self.client.force_authenticate(user=self.customer)
        data = {
            'items': [
                {'product_id': self.product.id, 'quantity': 2}
            ]
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], OrderStatus.PENDING)
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('2000.00'))
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_name'], self.product.name)

    def test_list_orders_authenticated(self):
        Order.objects.create(user=self.customer, total_amount=Decimal('1000.00'))
        Order.objects.create(user=self.other_customer, total_amount=Decimal('500.00'))

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(Decimal(response.data['results'][0]['total_amount']), Decimal('1000.00'))

    def test_order_detail_authenticated(self):
        order = Order.objects.create(user=self.customer, total_amount=Decimal('1000.00'))
        detail_url = reverse('orders:order-detail', kwargs={'order_id': order.id})

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], order.id)

        self.client.force_authenticate(user=self.other_customer)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_order_authenticated(self):
        order = Order.objects.create(user=self.customer, total_amount=Decimal('1000.00'))
        cancel_url = reverse('orders:order-cancel', kwargs={'order_id': order.id})

        self.client.force_authenticate(user=self.customer)
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], OrderStatus.CANCELED)

    def test_admin_list_orders(self):
        Order.objects.create(user=self.customer, total_amount=Decimal('1000.00'))
        Order.objects.create(user=self.other_customer, total_amount=Decimal('500.00'))

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_admin_update_order_status(self):
        order = Order.objects.create(user=self.customer, total_amount=Decimal('1000.00'))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
            subtotal=self.product.price,
        )

        status_url = reverse('orders-admin:admin-order-status', kwargs={'order_id': order.id})

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(status_url, data={'status': OrderStatus.PAID})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], OrderStatus.PAID)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)
