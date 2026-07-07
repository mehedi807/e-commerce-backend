from django.db import models


class ProductStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'


CATEGORY_TREE_CACHE_KEY = 'category_tree'
CATEGORY_TREE_CACHE_TTL = 60 * 60
