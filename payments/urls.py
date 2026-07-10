from django.urls import path
from payments import apis

urlpatterns = [
    path('initiate/', apis.PaymentInitiateAPI.as_view(), name='initiate'),
    path('bkash/execute/', apis.PaymentExecuteBkashAPI.as_view(), name='bkash-execute'),
    path('bkash/query/', apis.PaymentQueryBkashAPI.as_view(), name='bkash-query'),
    path('order/<int:order_id>/', apis.PaymentListAPI.as_view(), name='payment-list'),
    path('webhooks/stripe/', apis.StripeWebhookAPI.as_view(), name='stripe-webhook'),
    path('webhooks/bkash/', apis.BkashWebhookAPI.as_view(), name='bkash-webhook'),
]

