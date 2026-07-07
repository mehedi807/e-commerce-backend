from django.contrib.auth import authenticate

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication import selectors, services
from core.exceptions import ApplicationError


class UserRegisterAPI(APIView):
    permission_classes = [AllowAny]
    description = 'Register a new user and return JWT tokens.'

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(min_length=8, write_only=True)
        first_name = serializers.CharField(max_length=150)
        last_name = serializers.CharField(max_length=150)

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        email = serializers.EmailField()
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        created_at = serializers.DateTimeField()

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        user = services.user_create(**input_serializer.validated_data)

        return Response(
            {
                'user': self.OutputSerializer(user).data,
                'tokens': services.user_get_tokens(user=user),
            },
            status=status.HTTP_201_CREATED,
        )


class UserLoginAPI(APIView):
    permission_classes = [AllowAny]
    description = 'Authenticate a user and return JWT tokens.'

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(write_only=True)

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        email = serializers.EmailField()
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        is_active = serializers.BooleanField()
        is_staff = serializers.BooleanField()
        created_at = serializers.DateTimeField()

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=input_serializer.validated_data['email'],
            password=input_serializer.validated_data['password'],
        )

        if user is None:
            raise ApplicationError('Invalid email or password.', status_code=401)

        return Response({
            'user': self.OutputSerializer(user).data,
            'tokens': services.user_get_tokens(user=user),
        })


class UserMeAPI(APIView):
    permission_classes = [IsAuthenticated]
    description = 'Get the authenticated user profile.'

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        email = serializers.EmailField()
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        is_active = serializers.BooleanField()
        is_staff = serializers.BooleanField()
        created_at = serializers.DateTimeField()

    def get(self, request):
        return Response(self.OutputSerializer(request.user).data)
