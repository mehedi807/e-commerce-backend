from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from products.models import Category
from products.services import category_tree_invalidate_cache


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_category_cache(sender, **kwargs):
    category_tree_invalidate_cache()

