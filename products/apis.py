from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardLimitOffsetPagination
from products import selectors, services



class CategoryOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    parent = serializers.IntegerField(source='parent_id', allow_null=True)
    created_at = serializers.DateTimeField()


class ProductOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    sku = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()
    status = serializers.CharField()
    category = CategoryOutputSerializer(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()



class ProductListAPI(APIView):
    permission_classes = [AllowAny]
    description = 'List all active products with filtering and pagination.'

    class FilterSerializer(serializers.Serializer):
        status = serializers.CharField(required=False)
        category = serializers.IntegerField(required=False)
        min_price = serializers.DecimalField(
            max_digits=10, decimal_places=2, required=False,
        )
        max_price = serializers.DecimalField(
            max_digits=10, decimal_places=2, required=False,
        )
        search = serializers.CharField(required=False)

    OutputSerializer = ProductOutputSerializer

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        qs = selectors.product_list(filters=filter_serializer.validated_data)


        paginator = StandardLimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        output = self.OutputSerializer(page, many=True).data
        return paginator.get_paginated_response(output)


class ProductDetailAPI(APIView):
    permission_classes = [AllowAny]
    description = 'Get product details by ID.'

    OutputSerializer = ProductOutputSerializer

    def get(self, request, product_id):
        product = selectors.product_get_by_id(product_id=product_id)
        output = self.OutputSerializer(product).data
        return Response(output)



class CategoryListAPI(APIView):
    permission_classes = [AllowAny]
    description = 'List all categories (flat).'

    OutputSerializer = CategoryOutputSerializer

    def get(self, request):
        categories = selectors.category_list()
        output = self.OutputSerializer(categories, many=True).data
        return Response(output)


class CategoryTreeAPI(APIView):
    permission_classes = [AllowAny]
    description = 'Get the nested category tree (DFS traversal, Redis cached).'

    def get(self, request):
        tree = selectors.category_tree_get()
        return Response(tree)



class ProductCreateAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Create a new product (admin only).'

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=255)
        sku = serializers.CharField(max_length=100)
        description = serializers.CharField(required=False, default='')
        price = serializers.DecimalField(max_digits=10, decimal_places=2)
        stock = serializers.IntegerField(min_value=0)
        status = serializers.ChoiceField(choices=['active', 'inactive'])
        category_id = serializers.IntegerField(required=False, allow_null=True)

    OutputSerializer = ProductOutputSerializer

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        product = services.product_create(**input_serializer.validated_data)

        output = self.OutputSerializer(product).data
        return Response(output, status=status.HTTP_201_CREATED)


class ProductUpdateAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Update an existing product (admin only).'

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=255, required=False)
        sku = serializers.CharField(max_length=100, required=False)
        description = serializers.CharField(required=False)
        price = serializers.DecimalField(
            max_digits=10, decimal_places=2, required=False,
        )
        stock = serializers.IntegerField(min_value=0, required=False)
        status = serializers.ChoiceField(
            choices=['active', 'inactive'], required=False,
        )
        category_id = serializers.IntegerField(required=False, allow_null=True)

    OutputSerializer = ProductOutputSerializer

    def put(self, request, product_id):
        product = selectors.product_get_by_id(product_id=product_id)

        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        product = services.product_update(
            product=product,
            data=input_serializer.validated_data,
        )

        output = self.OutputSerializer(product).data
        return Response(output)


class ProductDeleteAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Delete a product (admin only).'

    def delete(self, request, product_id):
        product = selectors.product_get_by_id(product_id=product_id)
        services.product_delete(product=product)
        return Response(status=status.HTTP_204_NO_CONTENT)



class CategoryCreateAPI(APIView):
    permission_classes = [IsAdminUser]
    description = 'Create a new category (admin only).'

    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=255)
        description = serializers.CharField(required=False, default='')
        parent_id = serializers.IntegerField(required=False, allow_null=True)

    OutputSerializer = CategoryOutputSerializer

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        category = services.category_create(**input_serializer.validated_data)

        output = self.OutputSerializer(category).data
        return Response(output, status=status.HTTP_201_CREATED)
