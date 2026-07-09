from django.conf import settings
from django.db import models

from core.models import BaseModel
from orders.constants import OrderStatus
from orders.managers import OrderQuerySet
from products.models import Product


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True,
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )
    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.user.email} - {self.status}'


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'Item {self.product.name} (x{self.quantity}) for Order #{self.order.id}'
