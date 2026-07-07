from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class HealthCheckAPI(APIView):
    permission_classes = [AllowAny]
    description = "Checks health."

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
