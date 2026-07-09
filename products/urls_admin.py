from django.urls import path
from products import apis

product_patterns = [
    path('', apis.ProductCreateAPI.as_view(), name='admin-product-create'),
    path('<int:product_id>/update/', apis.ProductUpdateAPI.as_view(), name='admin-product-update'),
    path('<int:product_id>/delete/', apis.ProductDeleteAPI.as_view(), name='admin-product-delete'),
]

category_patterns = [
    path('', apis.CategoryCreateAPI.as_view(), name='admin-category-create'),
]
