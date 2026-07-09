from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardLimitOffsetPagination
from orders import selectors, services


class OrderItemOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(source='product.name')
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)


class OrderOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    user_email = serializers.CharField(source='user.email')
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.CharField()
    items = OrderItemOutputSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class OrderCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = 'Create a new order from a list of products and quantities.'

    class InputSerializer(serializers.Serializer):
        class ItemSerializer(serializers.Serializer):
            product_id = serializers.IntegerField()
            quantity = serializers.IntegerField(min_value=1)

        items = ItemSerializer(many=True, min_length=1)

    OutputSerializer = OrderOutputSerializer

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order = services.order_create(
            user=request.user,
            items=input_serializer.validated_data['items'],
        )

        order = selectors.order_get_by_id(order_id=order.id, user=request.user)

        output = self.OutputSerializer(order).data
        return Response(output, status=status.HTTP_201_CREATED)


class OrderListAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = "List the authenticated user's orders."

    OutputSerializer = OrderOutputSerializer

    def get(self, request):
        qs = selectors.order_list(user=request.user)

        paginator = StandardLimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        output = self.OutputSerializer(page, many=True).data
        return paginator.get_paginated_response(output)


class OrderDetailAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = 'Get order details for the authenticated user by ID.'

    OutputSerializer = OrderOutputSerializer

    def get(self, request, order_id):
        order = selectors.order_get_by_id(order_id=order_id, user=request.user)
        output = self.OutputSerializer(order).data
        return Response(output)


class OrderCancelAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = 'Cancel a pending order.'

    OutputSerializer = OrderOutputSerializer

    def post(self, request, order_id):
        order = selectors.order_get_by_id(order_id=order_id, user=request.user)
        order = services.order_cancel(order=order, user=request.user)
        output = self.OutputSerializer(order).data
        return Response(output)


class OrderAdminListAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'List all orders in the system (admin only).'

    OutputSerializer = OrderOutputSerializer

    def get(self, request):
        qs = selectors.order_list_admin()

        paginator = StandardLimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        output = self.OutputSerializer(page, many=True).data
        return paginator.get_paginated_response(output)


class OrderAdminDetailAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Get details of any order (admin only).'

    OutputSerializer = OrderOutputSerializer

    def get(self, request, order_id):
        order = selectors.order_get_by_id(order_id=order_id)
        output = self.OutputSerializer(order).data
        return Response(output)


class OrderAdminUpdateStatusAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Update status of any order (admin only).'

    class InputSerializer(serializers.Serializer):
        status = serializers.CharField()

    OutputSerializer = OrderOutputSerializer

    def post(self, request, order_id):
        order = selectors.order_get_by_id(order_id=order_id)

        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        order = services.order_admin_update_status(
            order=order,
            status=input_serializer.validated_data['status'],
        )

        output = self.OutputSerializer(order).data
        return Response(output)
