from django.conf import settings
from django.core.mail import send_mail

def send_email_verification_email(user, token):
    verification_url = (
        f"{settings.FRONTEND_URL}/verify-email/?token={token.token}"
    )

    send_mail(
        subject="Verify your email",
        message=(
            f"Hello {user.username},\n\n"
            f"Please verify your email using the link below:\n\n"
            f"{verification_url}\n\n"
            "This link is for verifying your email address."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_password_reset_email(user, token):
    reset_url = (
        f"{settings.FRONTEND_URL}/reset-password/?token={token.token}"
    )

    send_mail(
        subject="Reset your password",
        message=(
            f"Hello {user.username},\n\n"
            f"You can reset your password using the link below:\n\n"
            f"{reset_url}\n\n"
            "If you did not request a password reset, "
            "you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )