from collections import defaultdict
from decimal import Decimal
from typing import Optional

from django.core.cache import cache
from django.db import IntegrityError, transaction, models
from django.utils.text import slugify

from core.exceptions import ApplicationError
from core import services
from products.constants import CATEGORY_TREE_CACHE_KEY, CATEGORY_TREE_CACHE_TTL
from products.models import Category, Product


def _get_category(category_id: int) -> Category:
    try:
        return Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise ApplicationError('Category not found.', status_code=400)


def _get_unique_slug(name: str) -> str:
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Category.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    return slug


def product_create(
    *,
    name: str,
    sku: str,
    description: str = '',
    price: Decimal,
    stock: int,
    status: str,
    category_id: Optional[int] = None,
) -> Product:
    category = _get_category(category_id) if category_id is not None else None

    try:
        with transaction.atomic():
            product = Product(
                name=name,
                sku=sku,
                description=description,
                price=price,
                stock=stock,
                status=status,
                category=category,
            )
            product.full_clean()
            product.save()
    except IntegrityError:
        raise ApplicationError('A product with this SKU already exists.', status_code=400)

    return product


def product_update(*, product: Product, data: dict) -> Product:
    if 'category_id' in data:
        category_id = data.pop('category_id')
        data['category'] = _get_category(category_id) if category_id is not None else None

    updatable_fields = ['name', 'sku', 'description', 'price', 'stock', 'status', 'category']
    product, _ = services.model_update(instance=product, fields=updatable_fields, data=data)
    return product


def product_delete(*, product: Product) -> None:
    try:
        product.delete()
    except models.ProtectedError:
        raise ApplicationError('Cannot delete a product that has been ordered.', status_code=400)


def category_create(
    *,
    name: str,
    description: str = '',
    parent_id: Optional[int] = None,
) -> Category:
    parent = None
    if parent_id is not None:
        try:
            parent = Category.objects.get(id=parent_id)
        except Category.DoesNotExist:
            raise ApplicationError('Parent category not found.', status_code=400)

    with transaction.atomic():
        category = Category(
            name=name,
            slug=_get_unique_slug(name),
            description=description,
            parent=parent,
        )
        category.full_clean()
        category.save()

    category_tree_invalidate_cache()
    return category


def category_tree_build() -> list[dict]:
    categories = Category.objects.all().order_by('name')

    children_map: dict[Optional[int], list] = defaultdict(list)
    for cat in categories:
        children_map[cat.parent_id].append(cat)

    def _dfs(parent_id: Optional[int]) -> list[dict]:
        return [
            {
                'id': node.id,
                'name': node.name,
                'slug': node.slug,
                'description': node.description,
                'children': _dfs(node.id),
            }
            for node in children_map[parent_id]
        ]

    return _dfs(None)


def category_tree_invalidate_cache() -> None:
    cache.delete(CATEGORY_TREE_CACHE_KEY)
