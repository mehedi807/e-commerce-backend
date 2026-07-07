from django.core.cache import cache
from django.db.models import QuerySet

from core.exceptions import ApplicationError
from products.constants import CATEGORY_TREE_CACHE_KEY, CATEGORY_TREE_CACHE_TTL
from products.models import Category, Product
from products import services



def product_list(*, filters: dict | None = None) -> QuerySet[Product]:
    qs = Product.objects.select_related('category').all()
    return qs


def product_get_by_id(*, product_id: int) -> Product:
    try:
        return Product.objects.select_related('category').get(id=product_id)
    except Product.DoesNotExist:
        raise ApplicationError('Product not found.', status_code=404)



def category_list() -> QuerySet[Category]:
    return Category.objects.all()


def category_tree_get() -> list[dict]:
    tree = cache.get(CATEGORY_TREE_CACHE_KEY)
    if tree is not None:
        return tree

    tree = services.category_tree_build()
    cache.set(CATEGORY_TREE_CACHE_KEY, tree, CATEGORY_TREE_CACHE_TTL)
    return tree
