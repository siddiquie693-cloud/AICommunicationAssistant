from rest_framework.response import Response
from rest_framework.views import APIView

class HealthCheckAPIView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "AI Communication Assistant",
                "version": "0.1.0",
            }
        )
