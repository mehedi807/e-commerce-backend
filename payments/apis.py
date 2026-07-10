from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.pagination import StandardLimitOffsetPagination
from orders.selectors import order_get_by_id
from payments import selectors, services, constants


class PaymentOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    provider = serializers.CharField()
    transaction_id = serializers.CharField()
    status = serializers.CharField()
    raw_response = serializers.JSONField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PaymentInitiateAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "Initiate a payment for a pending order using Stripe or bKash."

    class InputSerializer(serializers.Serializer):
        order_id = serializers.IntegerField()
        provider = serializers.ChoiceField(choices=constants.PaymentProvider.choices)

    class OutputSerializer(serializers.Serializer):
        payment_id = serializers.IntegerField()
        transaction_id = serializers.CharField()
        client_secret = serializers.CharField(required=False, allow_null=True)
        bkash_url = serializers.URLField(required=False, allow_null=True)

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order_id = input_serializer.validated_data['order_id']
        provider = input_serializer.validated_data['provider']

        order = order_get_by_id(order_id=order_id, user=request.user)

        initiation_data = services.payment_initiate(order=order, provider=provider)
        output = self.OutputSerializer(initiation_data).data
        return Response(output, status=status.HTTP_201_CREATED)


class PaymentConfirmStripeAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "Manually check and confirm the status of a Stripe payment intent."

    class InputSerializer(serializers.Serializer):
        transaction_id = serializers.CharField()

    OutputSerializer = PaymentOutputSerializer

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        transaction_id = input_serializer.validated_data['transaction_id']

        payment = services.payment_confirm_stripe(transaction_id=transaction_id)
        if not request.user.is_staff and payment.order.user_id != request.user.id:
            return Response({"detail": "You do not have permission to access this payment."}, status=403)

        output = self.OutputSerializer(payment).data
        return Response(output)


class PaymentExecuteBkashAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "Manually execute/confirm a bKash payment."

    class InputSerializer(serializers.Serializer):
        payment_id = serializers.CharField()

    OutputSerializer = PaymentOutputSerializer

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        payment_id = input_serializer.validated_data['payment_id']

        payment = services.payment_execute_bkash(payment_id=payment_id)
        if not request.user.is_staff and payment.order.user_id != request.user.id:
            return Response({"detail": "You do not have permission to access this payment."}, status=403)

        output = self.OutputSerializer(payment).data
        return Response(output)


class PaymentQueryBkashAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "Query the status of a bKash payment from bKash server."

    class InputSerializer(serializers.Serializer):
        payment_id = serializers.CharField()

    class OutputSerializer(serializers.Serializer):
        paymentID = serializers.CharField()
        trxID = serializers.CharField(required=False, allow_null=True)
        amount = serializers.CharField()
        transactionStatus = serializers.CharField()
        merchantInvoiceNumber = serializers.CharField()
        statusCode = serializers.CharField()
        statusMessage = serializers.CharField()

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        payment_id = input_serializer.validated_data['payment_id']

        payment = selectors.payment_get_by_transaction_id(transaction_id=payment_id)
        if not request.user.is_staff and payment.order.user_id != request.user.id:
            return Response({"detail": "You do not have permission to access this payment."}, status=403)

        query_data = services.payment_query_bkash(payment_id=payment_id)
        output = self.OutputSerializer(query_data).data
        return Response(output)


class PaymentListAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "List all payments/attempts for a specific order."

    OutputSerializer = PaymentOutputSerializer

    def get(self, request, order_id):
        order = order_get_by_id(order_id=order_id, user=request.user)

        qs = selectors.payment_list_by_order(order_id=order.id)
        paginator = StandardLimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        output = self.OutputSerializer(page, many=True).data
        return paginator.get_paginated_response(output)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPI(APIView):
    permission_classes = [AllowAny]
    description = "Stripe webhook receiver."

    def post(self, request):
        sig_header = request.headers.get('stripe-signature') or request.META.get('HTTP_STRIPE_SIGNATURE')
        if not sig_header:
            return Response({"detail": "Missing signature header"}, status=status.HTTP_400_BAD_REQUEST)

        services.payment_handle_stripe_webhook(payload=request.body, sig_header=sig_header)
        return Response({"status": "received"}, status=status.HTTP_200_OK)


class BkashCallbackAPI(APIView):
    permission_classes = [AllowAny]
    description = "Redirect target for bKash payment checkout flow."

    def get(self, request):
        payment_id = request.query_params.get('paymentID')
        status_param = request.query_params.get('status')

        if not payment_id or not status_param:
            return Response({"detail": "Missing paymentID or status query parameters"}, status=status.HTTP_400_BAD_REQUEST)

        result = services.payment_handle_bkash_callback(payment_id=payment_id, status=status_param)
        
        frontend_url = settings.BKASH_FRONTEND_REDIRECT_URL.rstrip('?')
        redirect_target = f"{frontend_url}?status={result['status']}&paymentID={payment_id}"
        return HttpResponseRedirect(redirect_target)


@method_decorator(csrf_exempt, name='dispatch')
class BkashWebhookAPI(APIView):
    permission_classes = [AllowAny]
    description = "bKash Instant Payment Notification (IPN) webhook listener (AWS SNS format)."

    def post(self, request):
        services.payment_handle_bkash_webhook(payload=request.body, headers=request.META)
        return Response({"status": "received"}, status=status.HTTP_200_OK)
