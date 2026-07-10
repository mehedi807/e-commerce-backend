from django.db import models
from core.models import BaseModel
from orders.models import Order
from payments import constants


class Payment(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True,
    )
    provider = models.CharField(
        max_length=20,
        choices=constants.PaymentProvider.choices,
        db_index=True,
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=constants.PaymentStatus.choices,
        default=constants.PaymentStatus.PENDING,
        db_index=True,
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - Order #{self.order_id} - {self.provider} - {self.status}"
