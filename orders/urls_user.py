from django.urls import path
from orders import apis

urlpatterns = [
    path('', apis.OrderCreateAPI.as_view(), name='order-create'),
    path('list/', apis.OrderListAPI.as_view(), name='order-list'),
    path('<int:order_id>/', apis.OrderDetailAPI.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', apis.OrderCancelAPI.as_view(), name='order-cancel'),
]
