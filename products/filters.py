from django.db.models import Q
from django_filters import FilterSet, CharFilter, NumberFilter

from products.models import Product


class ProductFilter(FilterSet):
    status = CharFilter(field_name='status', lookup_expr='exact')
    category = NumberFilter(field_name='category_id', lookup_expr='exact')
    min_price = NumberFilter(field_name='price', lookup_expr='gte')
    max_price = NumberFilter(field_name='price', lookup_expr='lte')
    search = CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = ['status', 'category', 'min_price', 'max_price', 'search']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(sku__icontains=value)
        )

