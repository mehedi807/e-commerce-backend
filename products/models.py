from django.db import models
from django.utils.text import slugify

from core.models import BaseModel
from products.constants import ProductStatus


class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
    )

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        db_index=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.sku})'
