from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .capture import MemoryCaptureService

from .models import Memory
from ai.memory.types import MemoryQuery
from .services import MemoryService
from .serializers import MemorySerializer

from rest_framework.test import APIRequestFactory, force_authenticate

from .views import (
    MemoryDetailAPIView,
    MemoryListCreateAPIView,
)
from rest_framework.test import APIClient
User = get_user_model()


class MemoryModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="memoryuser",
            password="testpassword123",
        )

    def test_memory_can_be_created_for_user(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(memory.user, self.user)
        self.assertEqual(
            memory.content,
            "User prefers concise responses.",
        )
        self.assertEqual(
            memory.memory_type,
            Memory.MemoryType.PREFERENCE,
        )

    def test_memory_defaults_are_applied(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User works with Python.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertEqual(memory.importance, 3)
        self.assertTrue(memory.is_active)
        self.assertEqual(memory.metadata, {})
        self.assertIsNone(memory.expires_at)

    def test_memory_importance_accepts_values_from_one_to_five(self):
        for importance in range(1, 6):
            memory = Memory(
                user=self.user,
                content=f"Importance {importance}",
                memory_type=Memory.MemoryType.FACT,
                importance=importance,
            )

            memory.full_clean()

    def test_memory_importance_rejects_value_below_one(self):
        memory = Memory(
            user=self.user,
            content="Invalid low importance",
            memory_type=Memory.MemoryType.FACT,
            importance=0,
        )

        with self.assertRaises(ValidationError):
            memory.full_clean()

    def test_memory_importance_rejects_value_above_five(self):
        memory = Memory(
            user=self.user,
            content="Invalid high importance",
            memory_type=Memory.MemoryType.FACT,
            importance=6,
        )

        with self.assertRaises(ValidationError):
            memory.full_clean()

    def test_memory_supports_expiration(self):
        expires_at = timezone.now() + timedelta(days=7)

        memory = Memory.objects.create(
            user=self.user,
            content="Temporary context",
            memory_type=Memory.MemoryType.CONTEXT,
            expires_at=expires_at,
        )

        self.assertEqual(memory.expires_at, expires_at)

    def test_memory_can_be_deactivated_without_deletion(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers dark mode.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        memory.is_active = False
        memory.save(update_fields=["is_active"])

        self.assertFalse(memory.is_active)
        self.assertTrue(
            Memory.objects.filter(pk=memory.pk).exists()
        )

    def test_memory_supports_metadata(self):
        metadata = {
            "source": "conversation",
            "confidence": 0.95,
        }

        memory = Memory.objects.create(
            user=self.user,
            content="User is learning AI engineering.",
            memory_type=Memory.MemoryType.GOAL,
            metadata=metadata,
        )

        self.assertEqual(memory.metadata, metadata)

    def test_memory_belongs_to_only_its_owner(self):
        another_user = User.objects.create_user(
            username="anothermemoryuser",
            email="anothermemoryuser@example.com",
            password="testpassword123",
        )

        memory = Memory.objects.create(
            user=self.user,
            content="Private user memory",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertTrue(
            Memory.objects.filter(
                pk=memory.pk,
                user=self.user,
            ).exists()
        )
        self.assertFalse(
            Memory.objects.filter(
                pk=memory.pk,
                user=another_user,
            ).exists()
        )

    def test_memory_is_deleted_when_owner_is_deleted(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User-owned memory",
            memory_type=Memory.MemoryType.FACT,
        )

        memory_id = memory.pk
        self.user.delete()

        self.assertFalse(
            Memory.objects.filter(pk=memory_id).exists()
        )

    def test_memory_ordering_uses_newest_first(self):
        older = Memory.objects.create(
            user=self.user,
            content="Older memory",
            memory_type=Memory.MemoryType.FACT,
        )

        newer = Memory.objects.create(
            user=self.user,
            content="Newer memory",
            memory_type=Memory.MemoryType.FACT,
        )

        memories = list(Memory.objects.filter(user=self.user))

        self.assertEqual(memories[0], newer)
        self.assertEqual(memories[1], older)

    def test_memory_string_representation_uses_content(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise answers.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(
            str(memory),
            "User prefers concise answers.",
        )

class MemoryServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="memoryserviceuser",
            email="memoryserviceuser@example.com",
            password="testpassword123",
        )
        self.other_user = User.objects.create_user(
            username="othermemoryserviceuser",
            email="othermemoryserviceuser@example.com",
            password="testpassword123",
        )

    def test_create_memory_creates_user_owned_memory(self):
        memory = MemoryService.create_memory(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(memory.user, self.user)
        self.assertEqual(
            memory.content,
            "User prefers concise responses.",
        )

    def test_get_memory_returns_memory_for_owner(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Private memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.get_memory(
            user=self.user,
            memory_id=memory.id,
        )

        self.assertEqual(result, memory)

    def test_get_memory_does_not_return_memory_for_other_user(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Private memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.get_memory(
            user=self.other_user,
            memory_id=memory.id,
        )

        self.assertIsNone(result)

    def test_list_memories_returns_only_user_memories(self):
        own_memory = Memory.objects.create(
            user=self.user,
            content="Own memory",
            memory_type=Memory.MemoryType.FACT,
        )
        Memory.objects.create(
            user=self.other_user,
            content="Other user memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = list(
            MemoryService.list_memories(user=self.user)
        )

        self.assertEqual(result, [own_memory])

    def test_list_memories_excludes_inactive_memories_by_default(self):
        active_memory = Memory.objects.create(
            user=self.user,
            content="Active memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=True,
        )
        Memory.objects.create(
            user=self.user,
            content="Inactive memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=False,
        )

        result = list(
            MemoryService.list_memories(user=self.user)
        )

        self.assertEqual(result, [active_memory])

    def test_list_memories_can_include_inactive_memories(self):
        active_memory = Memory.objects.create(
            user=self.user,
            content="Active memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=True,
        )
        inactive_memory = Memory.objects.create(
            user=self.user,
            content="Inactive memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=False,
        )

        result = list(
            MemoryService.list_memories(
                user=self.user,
                include_inactive=True,
            )
        )

        self.assertCountEqual(
            result,
            [active_memory, inactive_memory],
        )

    def test_list_active_memories_excludes_expired_memories(self):
        active_memory = Memory.objects.create(
            user=self.user,
            content="Active memory",
            memory_type=Memory.MemoryType.FACT,
        )
        Memory.objects.create(
            user=self.user,
            content="Expired memory",
            memory_type=Memory.MemoryType.FACT,
            expires_at=timezone.now() - timedelta(days=1),
        )

        result = list(
            MemoryService.list_active_memories(user=self.user)
        )

        self.assertEqual(result, [active_memory])

    def test_list_active_memories_includes_non_expiring_memories(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Permanent memory",
            memory_type=Memory.MemoryType.FACT,
            expires_at=None,
        )

        result = list(
            MemoryService.list_active_memories(user=self.user)
        )

        self.assertEqual(result, [memory])

    def test_list_active_memories_excludes_inactive_memories(self):
        Memory.objects.create(
            user=self.user,
            content="Inactive memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=False,
        )

        result = list(
            MemoryService.list_active_memories(user=self.user)
        )

        self.assertEqual(result, [])

    def test_update_memory_updates_allowed_fields(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Original memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            content="Updated memory",
            importance=5,
            metadata={"source": "user"},
        )

        self.assertEqual(result.content, "Updated memory")
        self.assertEqual(result.importance, 5)
        self.assertEqual(
            result.metadata,
            {"source": "user"},
        )

    def test_update_memory_does_not_update_other_user_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Original memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.update_memory(
            user=self.other_user,
            memory_id=memory.id,
            content="Unauthorized update",
        )

        self.assertIsNone(result)
        memory.refresh_from_db()
        self.assertEqual(memory.content, "Original memory")

    def test_update_memory_returns_none_for_missing_memory(self):
        result = MemoryService.update_memory(
            user=self.user,
            memory_id=999999,
            content="Missing memory",
        )

        self.assertIsNone(result)

    def test_deactivate_memory_deactivates_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to deactivate",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.deactivate_memory(
            user=self.user,
            memory_id=memory.id,
        )

        self.assertEqual(result, memory)
        memory.refresh_from_db()
        self.assertFalse(memory.is_active)

    def test_deactivate_memory_does_not_deactivate_other_user_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Protected memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.deactivate_memory(
            user=self.other_user,
            memory_id=memory.id,
        )

        self.assertIsNone(result)
        memory.refresh_from_db()
        self.assertTrue(memory.is_active)

    def test_delete_memory_deletes_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to delete",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.delete_memory(
            user=self.user,
            memory_id=memory.id,
        )

        self.assertTrue(result)
        self.assertFalse(
            Memory.objects.filter(id=memory.id).exists()
        )

    def test_delete_memory_does_not_delete_other_user_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Protected memory",
            memory_type=Memory.MemoryType.FACT,
        )

        result = MemoryService.delete_memory(
            user=self.other_user,
            memory_id=memory.id,
        )

        self.assertFalse(result)
        self.assertTrue(
            Memory.objects.filter(id=memory.id).exists()
        )

    def test_delete_memory_returns_false_for_missing_memory(self):
        result = MemoryService.delete_memory(
            user=self.user,
            memory_id=999999,
        )

        self.assertFalse(result)

class DjangoMemoryRetrieverTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="memoryretrieveruser",
            email="memoryretriever@example.com",
            password="testpass123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="othermemoryretrieveruser",
            email="othermemoryretriever@example.com",
            password="testpass123",
        )

        from .retriever import DjangoMemoryRetriever

        self.retriever = DjangoMemoryRetriever()

    def test_retrieve_returns_memory_results_for_user(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        query = MemoryQuery(
            text="response preferences",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content)
        self.assertEqual(results[0].metadata["memory_id"], memory.id)

    def test_retrieve_does_not_return_other_users_memories(self):
        Memory.objects.create(
            user=self.other_user,
            content="Other user's private memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        query = MemoryQuery(
            text="private memory",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(results, [])

    def test_retrieve_excludes_inactive_memories(self):
        Memory.objects.create(
            user=self.user,
            content="Inactive memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
            is_active=False,
        )

        query = MemoryQuery(
            text="inactive",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(results, [])

    def test_retrieve_excludes_expired_memories(self):
        Memory.objects.create(
            user=self.user,
            content="Expired memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        query = MemoryQuery(
            text="expired",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(results, [])

    def test_retrieve_includes_non_expiring_memories(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Permanent memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=3,
        )

        query = MemoryQuery(
            text="permanent",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content)

    def test_retrieve_respects_limit(self):
        for index in range(4):
            Memory.objects.create(
                user=self.user,
                content=f"Memory {index}",
                memory_type=Memory.MemoryType.FACT,
                importance=index + 1,
            )

        query = MemoryQuery(
            text="memories",
            user_id=self.user.id,
            limit=2,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(len(results), 2)

    def test_retrieve_orders_memories_by_importance_then_recency(self):
        lower_importance = Memory.objects.create(
            user=self.user,
            content="Lower importance memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=2,
        )
        higher_importance = Memory.objects.create(
            user=self.user,
            content="Higher importance memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        query = MemoryQuery(
            text="important memories",
            user_id=self.user.id,
            limit=2,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(
            results[0].content,
            higher_importance.content,
        )
        self.assertEqual(
            results[1].content,
            lower_importance.content,
        )

    def test_retrieve_includes_memory_metadata(self):
        Memory.objects.create(
            user=self.user,
            content="Metadata memory.",
            memory_type=Memory.MemoryType.EVENT,
            importance=4,
            metadata={
                "source": "conversation",
                "channel": "whatsapp",
            },
        )

        query = MemoryQuery(
            text="metadata",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(
            results[0].metadata["source"],
            "conversation",
        )
        self.assertEqual(
            results[0].metadata["channel"],
            "whatsapp",
        )
        self.assertEqual(
            results[0].metadata["memory_type"],
            Memory.MemoryType.EVENT,
        )

    def test_retrieve_rejects_non_memory_query(self):
        with self.assertRaises(TypeError):
            self.retriever.retrieve("memory query")

    def test_retrieve_returns_empty_for_zero_limit(self):
        Memory.objects.create(
            user=self.user,
            content="Zero limit memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        query = MemoryQuery(
            text="memory",
            user_id=self.user.id,
            limit=0,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(results, [])

class MemoryCaptureServiceTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="memorycaptureuser",
            email="memorycaptureuser@example.com",
            password="testpassword123",
        )

    def test_capture_creates_memory_from_valid_candidate(self):
        memory = MemoryCaptureService.capture(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        self.assertIsNotNone(memory)
        self.assertEqual(memory.user, self.user)
        self.assertEqual(
            memory.content,
            "User prefers concise responses.",
        )
        self.assertEqual(
            memory.memory_type,
            Memory.MemoryType.PREFERENCE,
        )
        self.assertEqual(memory.importance, 4)

    def test_capture_strips_memory_content(self):
        memory = MemoryCaptureService.capture(
            user=self.user,
            content="  User prefers Hindi responses.  ",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(
            memory.content,
            "User prefers Hindi responses.",
        )

    def test_capture_returns_none_for_empty_content(self):
        memory = MemoryCaptureService.capture(
            user=self.user,
            content="",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertIsNone(memory)
        self.assertEqual(
            Memory.objects.filter(user=self.user).count(),
            0,
        )

    def test_capture_returns_none_for_whitespace_only_content(self):
        memory = MemoryCaptureService.capture(
            user=self.user,
            content="   ",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertIsNone(memory)
        self.assertEqual(
            Memory.objects.filter(user=self.user).count(),
            0,
        )

    def test_capture_preserves_memory_metadata(self):
        memory = MemoryCaptureService.capture(
            user=self.user,
            content="User works on backend development.",
            memory_type=Memory.MemoryType.FACT,
            metadata={
                "source": "user_statement",
                "confidence": 0.95,
            },
        )

        self.assertEqual(
            memory.metadata,
            {
                "source": "user_statement",
                "confidence": 0.95,
            },
        )

    def test_capture_preserves_expiration(self):
        expires_at = timezone.now() + timedelta(days=30)

        memory = MemoryCaptureService.capture(
            user=self.user,
            content="User has a temporary project deadline.",
            memory_type=Memory.MemoryType.TASK,
            expires_at=expires_at,
        )

        self.assertEqual(memory.expires_at, expires_at)

    def test_capture_does_not_create_memory_for_invalid_content(self):
        before_count = Memory.objects.filter(user=self.user).count()

        memory = MemoryCaptureService.capture(
            user=self.user,
            content=None,
            memory_type=Memory.MemoryType.FACT,
        )

        after_count = Memory.objects.filter(user=self.user).count()

        self.assertIsNone(memory)
        self.assertEqual(before_count, after_count)

    def test_capture_explicit_memory_marks_capture_mode(self):
        memory = MemoryCaptureService.capture_explicit_memory(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(
            memory.metadata["capture_mode"],
            "explicit",
        )

    def test_capture_explicit_memory_preserves_existing_metadata(self):
        memory = MemoryCaptureService.capture_explicit_memory(
            user=self.user,
            content="User works on AI projects.",
            memory_type=Memory.MemoryType.FACT,
            metadata={
                "source": "user_statement",
                "confidence": 1.0,
            },
        )

        self.assertEqual(
            memory.metadata,
            {
                "source": "user_statement",
                "confidence": 1.0,
                "capture_mode": "explicit",
            },
        )

    def test_capture_explicit_memory_strips_content(self):
        memory = MemoryCaptureService.capture_explicit_memory(
            user=self.user,
            content="  User prefers Python.  ",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(
            memory.content,
            "User prefers Python.",
        )

    def test_capture_explicit_memory_returns_none_for_empty_content(self):
        memory = MemoryCaptureService.capture_explicit_memory(
            user=self.user,
            content="   ",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertIsNone(memory)
        self.assertEqual(
            Memory.objects.filter(user=self.user).count(),
            0,
        )    

class MemorySerializerTestCase(TestCase):
    def test_serializer_accepts_valid_memory_data(self):
        serializer = MemorySerializer(
            data={
                "content": "User prefers concise responses.",
                "memory_type": Memory.MemoryType.PREFERENCE,
                "importance": 4,
                "metadata": {"source": "user_statement"},
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["content"],
            "User prefers concise responses.",
        )

    def test_serializer_strips_memory_content(self):
        serializer = MemorySerializer(
            data={
                "content": "  User prefers Python.  ",
                "memory_type": Memory.MemoryType.PREFERENCE,
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["content"],
            "User prefers Python.",
        )

    def test_serializer_rejects_empty_memory_content(self):
        serializer = MemorySerializer(
            data={
                "content": "   ",
                "memory_type": Memory.MemoryType.FACT,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)

    def test_serializer_rejects_invalid_memory_type(self):
        serializer = MemorySerializer(
            data={
                "content": "User likes Python.",
                "memory_type": "invalid_type",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("memory_type", serializer.errors)

    def test_serializer_rejects_importance_below_one(self):
        serializer = MemorySerializer(
            data={
                "content": "Low importance memory.",
                "memory_type": Memory.MemoryType.FACT,
                "importance": 0,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("importance", serializer.errors)

    def test_serializer_rejects_importance_above_five(self):
        serializer = MemorySerializer(
            data={
                "content": "High importance memory.",
                "memory_type": Memory.MemoryType.FACT,
                "importance": 6,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("importance", serializer.errors)

class MemoryAPIViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = get_user_model().objects.create_user(
            username="memoryapiuser",
            email="memoryapiuser@example.com",
            password="testpassword123",
        )

        self.other_user = get_user_model().objects.create_user(
            username="othermemoryapiuser",
            email="othermemoryapiuser@example.com",
            password="testpassword123",
        )

    def test_memory_list_requires_authentication(self):
        request = self.factory.get("/api/memories/")

        response = MemoryListCreateAPIView.as_view()(request)

        self.assertEqual(response.status_code, 401)

    def test_memory_list_returns_only_authenticated_users_memories(self):
        own_memory = Memory.objects.create(
            user=self.user,
            content="My memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        Memory.objects.create(
            user=self.other_user,
            content="Other user's memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.get("/api/memories/")
        force_authenticate(request, user=self.user)

        response = MemoryListCreateAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], own_memory.id)

    def test_memory_create_creates_authenticated_users_memory(self):
        request = self.factory.post(
            "/api/memories/",
            {
                "content": "User prefers concise responses.",
                "memory_type": Memory.MemoryType.PREFERENCE,
                "importance": 4,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = MemoryListCreateAPIView.as_view()(request)

        self.assertEqual(response.status_code, 201)

        memory = Memory.objects.get(
            id=response.data["id"],
        )

        self.assertEqual(memory.user, self.user)
        self.assertEqual(
            memory.content,
            "User prefers concise responses.",
        )

    def test_memory_create_rejects_invalid_data(self):
        request = self.factory.post(
            "/api/memories/",
            {
                "content": "",
                "memory_type": Memory.MemoryType.FACT,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = MemoryListCreateAPIView.as_view()(request)

        self.assertEqual(response.status_code, 400)

    def test_memory_detail_returns_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="My personal memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.get(
            f"/api/memories/{memory.id}/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], memory.id)

    def test_memory_detail_does_not_return_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Private memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.get(
            f"/api/memories/{memory.id}/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 404)

    def test_memory_detail_patch_updates_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Old memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.patch(
            f"/api/memories/{memory.id}/",
            {
                "content": "Updated memory.",
                "importance": 5,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 200)

        memory.refresh_from_db()

        self.assertEqual(
            memory.content,
            "Updated memory.",
        )
        self.assertEqual(memory.importance, 5)

    def test_memory_detail_patch_cannot_update_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Private memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.patch(
            f"/api/memories/{memory.id}/",
            {
                "content": "Attempted modification.",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 404)

        memory.refresh_from_db()

        self.assertEqual(
            memory.content,
            "Private memory.",
        )

    def test_memory_detail_post_deactivates_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to deactivate.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.post(
            f"/api/memories/{memory.id}/deactivate/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 200)

        memory.refresh_from_db()

        self.assertFalse(memory.is_active)

    def test_memory_detail_post_cannot_deactivate_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Other user's memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.post(
            f"/api/memories/{memory.id}/deactivate/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 404)

        memory.refresh_from_db()

        self.assertTrue(memory.is_active)

    def test_memory_detail_delete_deletes_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to delete.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.delete(
            f"/api/memories/{memory.id}/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Memory.objects.filter(id=memory.id).exists()
        )

    def test_memory_detail_delete_cannot_delete_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Private memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        request = self.factory.delete(
            f"/api/memories/{memory.id}/",
        )
        force_authenticate(request, user=self.user)

        response = MemoryDetailAPIView.as_view()(
            request,
            memory_id=memory.id,
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Memory.objects.filter(id=memory.id).exists()
        )

class MemoryURLIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            username="memoryurluser",
            email="memoryurluser@example.com",
            password="testpassword123",
        )

        self.other_user = get_user_model().objects.create_user(
            username="othermemoryurluser",
            email="othermemoryurluser@example.com",
            password="testpassword123",
        )

    def test_memory_list_url_returns_authenticated_users_memories(self):
        memory = Memory.objects.create(
            user=self.user,
            content="My routed memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/memories/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], memory.id)

    def test_memory_create_url_creates_memory(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/memories/",
            {
                "content": "User prefers Python.",
                "memory_type": Memory.MemoryType.PREFERENCE,
                "importance": 4,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Memory.objects.filter(
                user=self.user,
                content="User prefers Python.",
            ).exists()
        )

    def test_memory_detail_url_returns_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Owned routed memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/memories/{memory.id}/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], memory.id)

    def test_memory_detail_url_rejects_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Private routed memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/memories/{memory.id}/",
        )

        self.assertEqual(response.status_code, 404)

    def test_memory_deactivate_url_deactivates_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to deactivate.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/memories/{memory.id}/deactivate/",
        )

        self.assertEqual(response.status_code, 200)

        memory.refresh_from_db()

        self.assertFalse(memory.is_active)

    def test_memory_delete_url_deletes_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to delete.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            f"/api/memories/{memory.id}/",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Memory.objects.filter(id=memory.id).exists()
        )

class MemoryDeactivateAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            username="deactivateuser",
            email="deactivateuser@example.com",
            password="testpass123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="otherdeactivateuser",
            email="otherdeactivateuser@example.com",
            password="testpass123",
        )

    def test_memory_deactivate_url_deactivates_owned_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/memories/{memory.id}/deactivate/"
        )

        self.assertEqual(response.status_code, 200)

        memory.refresh_from_db()

        self.assertFalse(memory.is_active)

    def test_memory_deactivate_url_returns_deactivated_memory(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/memories/{memory.id}/deactivate/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], memory.id)
        self.assertFalse(response.data["is_active"])

    def test_memory_deactivate_url_rejects_other_users_memory(self):
        memory = Memory.objects.create(
            user=self.other_user,
            content="Private memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/memories/{memory.id}/deactivate/"
        )

        self.assertEqual(response.status_code, 404)

        memory.refresh_from_db()

        self.assertTrue(memory.is_active)

    def test_memory_deactivate_url_returns_not_found_for_missing_memory(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            "/api/memories/999999/deactivate/"
        )

        self.client.force_authenticate(user=self.user)

        self.assertEqual(response.status_code, 404)

    def test_memory_deactivate_url_requires_authentication(self):
        self.client.logout()

        memory = Memory.objects.create(
            user=self.user,
            content="Authentication test memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        response = self.client.post(
            f"/api/memories/{memory.id}/deactivate/"
        )

        self.assertIn(response.status_code, [401, 403])