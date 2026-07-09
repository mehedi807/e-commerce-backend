from django.urls import path
from products import apis

urlpatterns = [
    path('', apis.ProductListAPI.as_view(), name='product-list'),
    path('<int:product_id>/', apis.ProductDetailAPI.as_view(), name='product-detail'),
    path('categories/', apis.CategoryListAPI.as_view(), name='category-list'),
    path('categories/tree/', apis.CategoryTreeAPI.as_view(), name='category-tree'),
]
