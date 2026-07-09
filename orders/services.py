from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from authentication.models import User
from core.exceptions import ApplicationError
from orders.constants import OrderStatus
from orders.models import Order, OrderItem
from products.models import Product
from products.constants import ProductStatus


def order_create(*, user: User, items: list[dict]) -> Order:
    if not items:
        raise ApplicationError('Order must contain at least one item.')

    aggregated = defaultdict(int)
    for item in items:
        aggregated[item['product_id']] += item['quantity']
    items = [{'product_id': pid, 'quantity': qty} for pid, qty in aggregated.items()]

    with transaction.atomic():
        order = Order(user=user, status=OrderStatus.PENDING)

        order.full_clean()
        order.save()

        total_amount = Decimal('0.00')
        order_items = []

        product_ids = [item['product_id'] for item in items]
        products = Product.objects.filter(id__in=product_ids).select_for_update()
        product_map = {p.id: p for p in products}

        for item_data in items:
            product_id = item_data['product_id']
            quantity = item_data['quantity']

            if product_id not in product_map:
                raise ApplicationError(f'Product with ID {product_id} does not exist.')

            product = product_map[product_id]

            if product.status != ProductStatus.ACTIVE:
                raise ApplicationError(f'Product {product.name} is not active.')

            if product.stock < quantity:
                raise ApplicationError(
                    f'Insufficient stock for product {product.name}. Available: {product.stock}, Requested: {quantity}'
                )

            price = product.price
            subtotal = price * quantity
            total_amount += subtotal

            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price=price,
                subtotal=subtotal,
            )
            order_items.append(order_item)

        OrderItem.objects.bulk_create(order_items)

        order.total_amount = total_amount
        order.save(update_fields=['total_amount', 'updated_at'])

    return order


def order_cancel(*, order: Order, user: User) -> Order:
    if not user.is_staff and order.user_id != user.id:
        raise ApplicationError('You do not have permission to cancel this order.', status_code=403)

    if order.status != OrderStatus.PENDING:
        raise ApplicationError(f'Cannot cancel an order that is already in {order.status} status.')

    with transaction.atomic():
        order.status = OrderStatus.CANCELED
        order.save(update_fields=['status', 'updated_at'])

    return order


def order_reduce_stock(*, order: Order) -> None:
    with transaction.atomic():
        for item in order.items.select_related('product').all():
            product = Product.objects.select_for_update().get(id=item.product.id)

            if product.stock < item.quantity:
                raise ApplicationError(
                    f'Insufficient stock for product {product.name} during payment processing. '
                    f'Available: {product.stock}, Requested: {item.quantity}'
                )

            product.stock -= item.quantity
            product.save(update_fields=['stock', 'updated_at'])


def order_mark_paid(*, order: Order) -> Order:
    if order.status != OrderStatus.PENDING:
        raise ApplicationError(f'Cannot mark order as paid from {order.status} status.')

    with transaction.atomic():
        order_reduce_stock(order=order)
        order.status = OrderStatus.PAID
        order.save(update_fields=['status', 'updated_at'])

    return order


def order_restore_stock(*, order: Order) -> None:
    with transaction.atomic():
        for item in order.items.select_related('product').all():
            product = Product.objects.select_for_update().get(id=item.product.id)
            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])


def order_admin_update_status(*, order: Order, status: str) -> Order:
    if status not in OrderStatus.values:
        raise ApplicationError(f'Invalid order status: {status}')

    if order.status == OrderStatus.CANCELED:
        raise ApplicationError('Cannot transition from CANCELED state.')

    if order.status == OrderStatus.PAID and status == OrderStatus.PENDING:
        raise ApplicationError('Cannot revert a PAID order back to PENDING.')

    if order.status == status:
        return order

    with transaction.atomic():
        if status == OrderStatus.PAID:
            order = order_mark_paid(order=order)
        elif status == OrderStatus.CANCELED:
            if order.status == OrderStatus.PAID:
                order_restore_stock(order=order)
            order.status = OrderStatus.CANCELED
            order.save(update_fields=['status', 'updated_at'])

    return order

