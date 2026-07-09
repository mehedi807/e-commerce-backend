from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from products.urls_admin import product_patterns, category_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/core/', include(('core.urls', 'core'), namespace='core')),
    path('api/auth/', include(('authentication.urls', 'authentication'), namespace='authentication')),
    path('api/products/', include(('products.urls_user', 'products-user'), namespace='products')),
    path('api/admin/products/', include((product_patterns, 'products-admin'), namespace='products-admin')),
    path('api/admin/categories/', include((category_patterns, 'categories-admin'), namespace='categories-admin')),
    path('api/orders/', include(('orders.urls_user', 'orders-user'), namespace='orders')),
    path('api/admin/orders/', include(('orders.urls_admin', 'orders-admin'), namespace='orders-admin')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

