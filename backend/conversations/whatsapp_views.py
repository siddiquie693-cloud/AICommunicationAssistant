from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from ai.whatsapp.exceptions import (
    WhatsAppProviderError,
    WhatsAppWebhookError,
)
from ai.whatsapp.factory import get_whatsapp_provider
from ai.whatsapp.service import WhatsAppService
from conversations.services.whatsapp_conversation_service import (
    WhatsAppConversationService,
)

class WhatsAppWebhookAPIView(APIView):
    """
    Handles WhatsApp webhook verification and incoming messages.
    """

    authentication_classes = []
    permission_classes = []

    def get_whatsapp_service(self):
        provider = get_whatsapp_provider()
        return WhatsAppService(provider)

    def get(self, request, *args, **kwargs):
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        expected_token = getattr(
            settings,
            "WHATSAPP_VERIFY_TOKEN",
            "",
        )

        if token != expected_token:
            return Response(
                {
                    "error": {
                        "code": "whatsapp_webhook_verification_failed",
                        "message": "Invalid webhook verification token.",
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            whatsapp_service = self.get_whatsapp_service()

            challenge_response = whatsapp_service.verify_webhook(
                mode,
                token,
                challenge,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "whatsapp_webhook_verification_failed",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except WhatsAppWebhookError:
            return Response(
                {
                    "error": {
                        "code": "whatsapp_webhook_verification_failed",
                        "message": "Unable to verify WhatsApp webhook.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return HttpResponse(
            challenge_response,
            status=status.HTTP_200_OK,
            content_type="text/plain",
        )

    def post(self, request, *args, **kwargs):
        try:
            whatsapp_service = self.get_whatsapp_service()

            payload = whatsapp_service.parse_webhook_message(
                request.data,
            )

            if not payload:
                return Response(
                    {
                        "success": True,
                        "payload": {},
                    },
                    status=status.HTTP_200_OK,
                )

            conversation_service = WhatsAppConversationService(
                whatsapp_service,
            )

            user = conversation_service.get_user_by_whatsapp_number(
                payload["sender"],
            )

            result = conversation_service.process_message(
                user,
                payload["sender"],
                payload["message"],
            )

        except ValueError as exc:
            return Response(
                {
                    "error": {
                        "code": "whatsapp_webhook_error",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except WhatsAppProviderError:
            return Response(
                {
                    "error": {
                        "code": "whatsapp_provider_error",
                        "message": "WhatsApp provider is currently unavailable.",
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "success": True,
                "payload": {
                    "message_id": payload["message_id"],
                    "conversation_id": result["conversation"].id,
                    "user_message_id": result["user_message"].id,
                    "assistant_message_id": result["assistant_message"].id,
                },
            },
            status=status.HTTP_200_OK,
        )