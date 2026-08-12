from rest_framework import status
from rest_framework.test import APITestCase

class HealthCheckAPITestCase(APITestCase):
    def test_health_check(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(
            response.data["service"],
            "AI Communication Assistant",
        )
        self.assertEqual(response.data["version"], "0.1.0")
