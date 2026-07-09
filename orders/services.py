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
        products = Product.objects.filter(id__in=product_ids).order_by('id').select_for_update()
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
    with transaction.atomic():
        db_order = Order.objects.select_for_update().get(id=order.id)

        if not user.is_staff and db_order.user_id != user.id:
            raise ApplicationError('You do not have permission to cancel this order.', status_code=403)

        if db_order.status != OrderStatus.PENDING:
            raise ApplicationError(f'Cannot cancel an order that is already in {db_order.status} status.')

        db_order.status = OrderStatus.CANCELED
        db_order.save(update_fields=['status', 'updated_at'])
        order.status = db_order.status

    return db_order


def order_reduce_stock(*, order: Order) -> None:
    with transaction.atomic():
        items = order.items.all()
        item_map = {item.product_id: item.quantity for item in items}
        #sort to prevent deadlock
        product_ids = sorted(list(item_map.keys()))

        products = Product.objects.filter(id__in=product_ids).order_by('id').select_for_update()
        product_map = {p.id: p for p in products}

        for item in items:
            product = product_map.get(item.product_id)
            if not product:
                raise ApplicationError(f'Product with ID {item.product_id} does not exist.')

            if product.stock < item.quantity:
                raise ApplicationError(
                    f'Insufficient stock for product {product.name} during payment processing. '
                    f'Available: {product.stock}, Requested: {item.quantity}'
                )

            product.stock -= item.quantity
            product.save(update_fields=['stock', 'updated_at'])


def order_mark_paid(*, order: Order) -> Order:
    with transaction.atomic():
        db_order = Order.objects.select_for_update().get(id=order.id)

        if db_order.status != OrderStatus.PENDING:
            raise ApplicationError(f'Cannot mark order as paid from {db_order.status} status.')

        order_reduce_stock(order=db_order)
        db_order.status = OrderStatus.PAID
        db_order.save(update_fields=['status', 'updated_at'])
        order.status = db_order.status

    return db_order


def order_restore_stock(*, order: Order) -> None:
    with transaction.atomic():
        items = order.items.all()
        product_ids = sorted(list({item.product_id for item in items}))

        products = Product.objects.filter(id__in=product_ids).order_by('id').select_for_update()
        product_map = {p.id: p for p in products}

        for item in items:
            product = product_map.get(item.product_id)
            if not product:
                raise ApplicationError(f'Product with ID {item.product_id} does not exist.')

            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])


def order_admin_update_status(*, order: Order, status: str) -> Order:
    if status not in OrderStatus.values:
        raise ApplicationError(f'Invalid order status: {status}')

    with transaction.atomic():
        db_order = Order.objects.select_for_update().get(id=order.id)

        if db_order.status == OrderStatus.CANCELED:
            raise ApplicationError('Cannot transition from CANCELED state.')

        if db_order.status == OrderStatus.PAID and status == OrderStatus.PENDING:
            raise ApplicationError('Cannot revert a PAID order back to PENDING.')

        if db_order.status == status:
            return db_order

        if status == OrderStatus.PAID:
            db_order = order_mark_paid(order=db_order)
        elif status == OrderStatus.CANCELED:
            if db_order.status == OrderStatus.PAID:
                order_restore_stock(order=db_order)
            db_order.status = OrderStatus.CANCELED
            db_order.save(update_fields=['status', 'updated_at'])

        order.status = db_order.status

    return db_order

