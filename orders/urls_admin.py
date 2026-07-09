from django.urls import path
from orders import apis

urlpatterns = [
    path('', apis.OrderAdminListAPI.as_view(), name='admin-order-list'),
    path('<int:order_id>/', apis.OrderAdminDetailAPI.as_view(), name='admin-order-detail'),
    path('<int:order_id>/status/', apis.OrderAdminUpdateStatusAPI.as_view(), name='admin-order-status'),
]
