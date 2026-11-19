
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from confirmations.models import PendingConfirmation
from ai.brain.types import PendingActionConfirmation


class ConfirmationStore:
    DEFAULT_EXPIRY = timedelta(minutes=5)

    def create_pending(
        self,
        *,
        user,
        confirmation: PendingActionConfirmation,
        expires_in=None,
    ):
        if user is None or not user.is_authenticated:
            raise ValueError("An authenticated user is required.")

        if not isinstance(confirmation, PendingActionConfirmation):
            raise TypeError(
                "confirmation must be a PendingActionConfirmation."
            )

        duration = expires_in or self.DEFAULT_EXPIRY

        if not isinstance(duration, timedelta) or duration.total_seconds() <= 0:
            raise ValueError("expires_in must be a positive duration.")

        return PendingConfirmation.objects.create(
            confirmation_id=confirmation.confirmation_id,
            user=user,
            action_name=confirmation.action_name,
            parameters=confirmation.parameters,
            reason=confirmation.reason,
            expires_at=timezone.now() + duration,
        )

    def get_pending(self, *, user, confirmation_id):
        if user is None or not user.is_authenticated:
            raise ValueError("An authenticated user is required.")

        now = timezone.now()

        with transaction.atomic():
            record = (
                PendingConfirmation.objects
                .select_for_update()
                .filter(
                    confirmation_id=confirmation_id,
                    user=user,
                    status=PendingConfirmation.Status.PENDING,
                )
                .first()
            )

            if record is None:
                return None

            if now >= record.expires_at:
                record.status = PendingConfirmation.Status.EXPIRED
                record.resolved_at = now
                record.save(
                    update_fields=["status", "resolved_at"]
                )
                return None

            return record

    def resolve(
        self,
        *,
        user,
        confirmation_id,
        approved,
    ):
        if user is None or not user.is_authenticated:
            raise ValueError("An authenticated user is required.")

        if not isinstance(approved, bool):
            raise TypeError("approved must be a boolean.")

        now = timezone.now()

        with transaction.atomic():
            record = (
                PendingConfirmation.objects
                .select_for_update()
                .filter(
                    confirmation_id=confirmation_id,
                    user=user,
                    status=PendingConfirmation.Status.PENDING,
                )
                .first()
            )

            if record is None:
                return None

            if now >= record.expires_at:
                record.status = PendingConfirmation.Status.EXPIRED
            elif approved:
                record.status = PendingConfirmation.Status.APPROVED
            else:
                record.status = PendingConfirmation.Status.REJECTED

            record.resolved_at = now
            record.save(
                update_fields=["status", "resolved_at"]
            )

            return record

    def consume_approved(
        self,
        *,
        user,
        confirmation_id,
    ):
        """
        Atomically consume an approved confirmation exactly once.
        """

        if user is None or not user.is_authenticated:
            raise ValueError("An authenticated user is required.")

        now = timezone.now()

        with transaction.atomic():
            record = (
                PendingConfirmation.objects
                .select_for_update()
                .filter(
                    confirmation_id=confirmation_id,
                    user=user,
                    status=PendingConfirmation.Status.APPROVED,
                )
                .first()
            )

            if record is None:
                return None

            if now >= record.expires_at:
                record.status = PendingConfirmation.Status.EXPIRED
                record.save(update_fields=["status"])
                return None

            record.status = PendingConfirmation.Status.CONSUMED
            record.save(update_fields=["status"])

            return record