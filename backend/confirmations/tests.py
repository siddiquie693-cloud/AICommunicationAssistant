
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ai.brain.types import PendingActionConfirmation
from confirmations.models import PendingConfirmation
from confirmations.store import ConfirmationStore


User = get_user_model()


class ConfirmationStoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nira_test",
            email="nira_test@example.com",
            password="test-password",
        )
        self.other_user = User.objects.create_user(
            username="other_test",
            email="other_test@example.com",
            password="test-password",
        )
        self.store = ConfirmationStore()

        self.confirmation = PendingActionConfirmation(
            confirmation_id="test-confirmation-123",
            action_name="send_message",
            parameters={
                "recipient": "Alex",
                "content": "Hello",
            },
            reason="Sending a message requires approval.",
        )

    def test_create_pending_confirmation(self):
        record = self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        self.assertEqual(record.user, self.user)
        self.assertEqual(record.status, PendingConfirmation.Status.PENDING)
        self.assertEqual(record.action_name, "send_message")

    def test_get_pending_confirmation(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        record = self.store.get_pending(
            user=self.user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.confirmation_id, "test-confirmation-123")

    def test_other_user_cannot_get_confirmation(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        record = self.store.get_pending(
            user=self.other_user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNone(record)

    def test_approve_confirmation(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        record = self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        self.assertEqual(record.status, PendingConfirmation.Status.APPROVED)

    def test_reject_confirmation(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        record = self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=False,
        )

        self.assertEqual(record.status, PendingConfirmation.Status.REJECTED)

    def test_confirmation_cannot_be_resolved_twice(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        first = self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )
        second = self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_expired_confirmation_cannot_be_approved(self):
        record = self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
            expires_in=timedelta(seconds=1),
        )

        PendingConfirmation.objects.filter(pk=record.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        result = self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        self.assertEqual(result.status, PendingConfirmation.Status.EXPIRED)

    
    def test_approved_confirmation_can_be_consumed_once(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        record = self.store.consume_approved(
            user=self.user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNotNone(record)
        self.assertEqual(
            record.status,
            PendingConfirmation.Status.CONSUMED,
        )

    def test_confirmation_cannot_be_consumed_twice(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        first = self.store.consume_approved(
            user=self.user,
            confirmation_id="test-confirmation-123",
        )

        second = self.store.consume_approved(
            user=self.user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_other_user_cannot_consume_approved_confirmation(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=True,
        )

        record = self.store.consume_approved(
            user=self.other_user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNone(record)

    def test_rejected_confirmation_cannot_be_consumed(self):
        self.store.create_pending(
            user=self.user,
            confirmation=self.confirmation,
        )

        self.store.resolve(
            user=self.user,
            confirmation_id="test-confirmation-123",
            approved=False,
        )

        record = self.store.consume_approved(
            user=self.user,
            confirmation_id="test-confirmation-123",
        )

        self.assertIsNone(record)
    

    def test_rejects_non_boolean_approval(self):
        with self.assertRaises(TypeError):
            self.store.resolve(
                user=self.user,
                confirmation_id="test-confirmation-123",
                approved="yes",
            )