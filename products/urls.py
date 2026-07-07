from django.urls import path
from products import apis

urlpatterns = [
    path('', apis.ProductListAPI.as_view(), name='product-list'),
    path('<int:product_id>/', apis.ProductDetailAPI.as_view(), name='product-detail'),
    path('categories/', apis.CategoryListAPI.as_view(), name='category-list'),
    path('categories/tree/', apis.CategoryTreeAPI.as_view(), name='category-tree'),

    path('admin/products/', apis.ProductCreateAPI.as_view(), name='admin-product-create'),
    path('admin/products/<int:product_id>/update/', apis.ProductUpdateAPI.as_view(), name='admin-product-update'),
    path('admin/products/<int:product_id>/delete/', apis.ProductDeleteAPI.as_view(), name='admin-product-delete'),
    path('admin/categories/', apis.CategoryCreateAPI.as_view(), name='admin-category-create'),
]
