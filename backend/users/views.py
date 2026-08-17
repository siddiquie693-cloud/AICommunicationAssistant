from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from .services import (
    send_email_verification_email,
    send_password_reset_email,
)

from .serializers import (
    LogoutSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    EmailVerificayionSerializer,
    ForgotPasswordSerializer,
    PasswordResetTokenSerializer,
    ResetPasswordSerializer,
    EmailVerificationTokenSerializer,
)

from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationAPIVIew(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            token_serializer = EmailVerificationTokenSerializer()
            verification_token = token_serializer.create_token(user)

            send_email_verification_email(
                user,
                verification_token,
            )

            return Response(
                {
                    "message": "User registered successfully.",
                    "user": UserRegistrationSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class CurentUserAPIVIew(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserRegistrationSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Successfully logged out."
            },
            status=status.HTTP_200_OK,
        )

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Password changed successfully."
            },
            status=status.HTTP_200_OK,
        )

class EmailVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificayionSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        verification_token = serializer.verification_token
        user = verification_token.user

        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.save(
            update_fields=[
                "email_verified",
                "email_verified_at",
            ]
        )

        verification_token.used = True
        verification_token.save(
            update_fields=["used"]
        )

        return Response(
            {
                "message": "Email verified successfully."
            },
            status=status.HTTP_200_OK,
        )

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email=email,
            is_active=True,
        ).first()

        if user:
            token_serializer = PasswordResetTokenSerializer()
            reset_token = token_serializer.create_token(user)

            send_password_reset_email(user, reset_token)

        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Password reset successfully."
            },
            status=status.HTTP_200_OK,
        )                                