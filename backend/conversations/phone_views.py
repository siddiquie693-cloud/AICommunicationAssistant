from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.phone.exceptions import PhoneProviderError, PhoneWebhookError
from ai.phone.factory import get_phone_provider
from ai.phone.service import PhoneService


class PhoneWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_phone_service(self):
        provider = get_phone_provider()
        return PhoneService(provider)

    def post(self, request, *args, **kwargs):
        try:
            phone_service = self.get_phone_service()

            payload = phone_service.handle_incoming_call(
                request.data,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "phone_webhook_error",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except PhoneWebhookError:
            return Response(
                {
                    "error": {
                        "code": "phone_webhook_error",
                        "message": "Invalid phone webhook payload.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except PhoneProviderError:
            return Response(
                {
                    "error": {
                        "code": "phone_provider_error",
                        "message": "Phone provider is currently unavailable.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "success": True,
                "payload": payload,
            },
            status=status.HTTP_200_OK,
        )

class PhoneCallAPIView(APIView):
    def post(self, request, *args, **kwargs):
        recipient = request.data.get("recipient")
        text = request.data.get("text")

        try:
            phone_service = PhoneService(
                get_phone_provider()
            )

            twiml = phone_service.generate_call_response(text)

            result = phone_service.make_call(
                recipient,
                twiml,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "phone_call_error",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except PhoneProviderError:
            return Response(
                {
                    "error": {
                        "code": "phone_provider_error",
                        "message": "Phone provider is currently unavailable.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "success": True,
                "call": result,
            },
            status=status.HTTP_200_OK,
        )    