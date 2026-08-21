from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: dict},
    )
    
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "AI Communication Assistant",
                "version": "0.1.0",
            }
        )
