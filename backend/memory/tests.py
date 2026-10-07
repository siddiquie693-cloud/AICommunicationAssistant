from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .capture import MemoryCaptureService
from people.models import Person

from .models import Memory
from ai.memory.types import MemoryQuery
from .services import MemoryService
from .retriever import DjangoMemoryRetriever
from .serializers import MemorySerializer
from ai.memory.types import MemoryQuery

from rest_framework.test import APIRequestFactory, force_authenticate

from .views import (
    MemoryDeactivateAPIView,
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

    def test_memory_can_be_linked_to_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(memory.person, person)

    def test_memory_person_is_optional(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertIsNone(memory.person)

    def test_deleting_person_preserves_memory(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Rahul works with Python.",
            memory_type=Memory.MemoryType.FACT,
        )

        memory_id = memory.id
        person.delete()

        memory.refresh_from_db()

        self.assertTrue(
            Memory.objects.filter(id=memory_id).exists()
        )
        self.assertIsNone(memory.person)

    def test_memory_person_relation_is_user_scoped_by_data_model(self):
        other_user = User.objects.create_user(
            username="memorypersonotheruser",
            email="memorypersonotheruser@example.com",
            password="testpassword123",
        )

        person = Person.objects.create(
            user=other_user,
            name="Other User Person",
        )

        memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Cross-owner memory.",
            memory_type=Memory.MemoryType.FACT,
        )

        self.assertEqual(memory.user, self.user)
        self.assertEqual(memory.person, person)
        self.assertNotEqual(memory.user_id, memory.person.user_id)    

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

    def test_create_memory_can_link_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        self.assertEqual(memory.person, person)

    def test_create_memory_rejects_person_from_another_user(self):
        person = Person.objects.create(
            user=self.other_user,
            name="Other User Person",
        )

        with self.assertRaises(ValueError):
            MemoryService.create_memory(
                user=self.user,
                person=person,
                content="Unauthorized person memory.",
                memory_type=Memory.MemoryType.FACT,
            )

    def test_create_memory_rejects_invalid_person_value(self):
        with self.assertRaises(ValueError):
            MemoryService.create_memory(
                user=self.user,
                person="not-a-person",
                content="Invalid person memory.",
                memory_type=Memory.MemoryType.FACT,
            )    

    def test_get_memories_for_person_returns_only_person_memories(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        person_memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        MemoryService.create_memory(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        memories = MemoryService.get_memories_for_person(
            user=self.user,
            person=person,
        )

        self.assertEqual(memories.count(), 1)
        self.assertEqual(memories[0].id, person_memory.id)

    def test_get_memories_for_person_excludes_inactive_memories(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        active_memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul likes Python.",
            memory_type=Memory.MemoryType.FACT,
        )

        inactive_memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul used to like Java.",
            memory_type=Memory.MemoryType.FACT,
        )

        inactive_memory.is_active = False
        inactive_memory.save(update_fields=["is_active"])

        memories = MemoryService.get_memories_for_person(
            user=self.user,
            person=person,
        )

        self.assertEqual(memories.count(), 1)
        self.assertEqual(memories[0].id, active_memory.id)

    def test_get_memories_for_person_respects_limit(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        for index in range(3):
            MemoryService.create_memory(
                user=self.user,
                person=person,
                content=f"Rahul memory {index}",
                memory_type=Memory.MemoryType.FACT,
            )

        memories = MemoryService.get_memories_for_person(
            user=self.user,
            person=person,
            limit=2,
        )

        self.assertEqual(memories.count(), 2)

    def test_get_memories_for_person_rejects_person_from_another_user(self):
        person = Person.objects.create(
            user=self.other_user,
            name="Other User Person",
        )

        with self.assertRaises(ValueError):
            MemoryService.get_memories_for_person(
                user=self.user,
                person=person,
            )

    def test_get_memories_for_person_rejects_invalid_person_value(self):
        with self.assertRaises(ValueError):
            MemoryService.get_memories_for_person(
                user=self.user,
                person="not-a-person",
            )  

    def test_update_memory_can_assign_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        updated_memory = MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            person=person,
        )

        self.assertEqual(updated_memory.person, person)

    def test_update_memory_can_reassign_person(self):
        first_person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )
        second_person = Person.objects.create(
            user=self.user,
            name="Amit",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=first_person,
            content="Contact prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        updated_memory = MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            person=second_person,
        )

        self.assertEqual(updated_memory.person, second_person)

    def test_update_memory_can_remove_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        updated_memory = MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            person=None,
        )

        self.assertIsNone(updated_memory.person)

    def test_update_memory_rejects_person_from_another_user(self):
        person = Person.objects.create(
            user=self.other_user,
            name="Other User Person",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            content="User preference.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        with self.assertRaises(ValueError):
            MemoryService.update_memory(
                user=self.user,
                memory_id=memory.id,
                person=person,
            )

    def test_update_memory_rejects_invalid_person_value(self):
        memory = MemoryService.create_memory(
            user=self.user,
            content="User preference.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        with self.assertRaises(ValueError):
            MemoryService.update_memory(
                user=self.user,
                memory_id=memory.id,
                person="not-a-person",
            )       

    def test_get_memory_preserves_memory_after_person_deletion(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul prefers WhatsApp.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        memory_id = memory.id
        person.delete()

        preserved_memory = MemoryService.get_memory(
            user=self.user,
            memory_id=memory_id,
        )

        self.assertIsNotNone(preserved_memory)
        self.assertEqual(preserved_memory.id, memory_id)
        self.assertIsNone(preserved_memory.person)

    def test_list_memories_preserves_memory_after_person_deletion(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul works with Python.",
            memory_type=Memory.MemoryType.FACT,
        )

        memory_id = memory.id
        person.delete()

        memories = MemoryService.list_memories(
            user=self.user,
        )

        self.assertEqual(memories.count(), 1)
        self.assertEqual(memories[0].id, memory_id)
        self.assertIsNone(memories[0].person)

    def test_list_active_memories_preserves_memory_after_person_deletion(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        memory = MemoryService.create_memory(
            user=self.user,
            person=person,
            content="Rahul likes Python.",
            memory_type=Memory.MemoryType.FACT,
        )

        memory_id = memory.id
        person.delete()

        memories = MemoryService.list_active_memories(
            user=self.user,
        )

        self.assertEqual(memories.count(), 1)
        self.assertEqual(memories[0].id, memory_id)
        self.assertIsNone(memories[0].person)         
      
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
            text="concise responses",
            user_id=self.user.id,
        )

        results = self.retriever.retrieve(query)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content)
        self.assertEqual(results[0].metadata["memory_id"], memory.id)

    def test_retrieve_matches_memory_content_case_insensitively(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="CONCISE RESPONSES",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content)


    def test_retrieve_excludes_memories_without_query_match(self):
        Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )
        Memory.objects.create(
            user=self.user,
            content="User works with Python.",
            memory_type=Memory.MemoryType.FACT,
            importance=4,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="Python",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "User works with Python.")


    def test_retrieve_matches_query_across_memory_content(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses when discussing technical topics.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="technical topics",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content)

    def test_retrieve_returns_empty_for_empty_query(self):
        Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="",
                user_id=self.user.id,
            )
        )

        self.assertEqual(results, [])


    def test_retrieve_returns_empty_for_whitespace_query(self):
        Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="   ",
                user_id=self.user.id,
            )
        )

        self.assertEqual(results, []) 

    def test_retrieve_orders_matching_memories_by_importance(self):
        lower_importance = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=2,
        )
        higher_importance = Memory.objects.create(
            user=self.user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )
        unrelated_memory = Memory.objects.create(
            user=self.user,
            content="User enjoys weekend hiking.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="responses",
                user_id=self.user.id,
                limit=2,
            )
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].content,
            higher_importance.content,
        )
        self.assertEqual(
            results[1].content,
            lower_importance.content,
        )
        self.assertNotIn(
            unrelated_memory.content,
            [result.content for result in results],
        ) 

    def test_retrieve_excludes_matching_expired_memory(self):
        active_memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )
        Memory.objects.create(
            user=self.user,
            content="User prefers detailed responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="responses",
                user_id=self.user.id,
                limit=5,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, active_memory.content)


    def test_retrieve_excludes_matching_inactive_memory(self):
        active_memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )
        Memory.objects.create(
            user=self.user,
            content="User prefers detailed responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            is_active=False,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="responses",
                user_id=self.user.id,
                limit=5,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, active_memory.content)  

    def test_retrieve_excludes_matching_memory_from_other_user(self):
        own_memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )
        Memory.objects.create(
            user=self.other_user,
            content="Other user prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="concise responses",
                user_id=self.user.id,
                limit=5,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, own_memory.content)


    def test_retrieve_returns_only_matching_memories_for_requested_user(self):
        own_matching_memory = Memory.objects.create(
            user=self.user,
            content="User works with Python backend development.",
            memory_type=Memory.MemoryType.FACT,
            importance=4,
        )
        Memory.objects.create(
            user=self.user,
            content="User enjoys weekend hiking.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )
        Memory.objects.create(
            user=self.other_user,
            content="Other user works with Python backend development.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="Python backend",
                user_id=self.user.id,
                limit=5,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].content,
            own_matching_memory.content,
        )

    def test_retrieve_matches_memory_when_query_terms_appear_separately(self):
        memory = Memory.objects.create(
            user=self.user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="concise responses",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, memory.content) 

    def test_retrieve_prioritizes_memory_matching_more_query_terms(self):
        partial_match = Memory.objects.create(
            user=self.user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )
        full_match = Memory.objects.create(
            user=self.user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        results = self.retriever.retrieve(
            MemoryQuery(
                text="concise technical responses",
                user_id=self.user.id,
                limit=2,
            )
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, full_match.content)
        self.assertEqual(results[1].content, partial_match.content)       

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

    def test_retrieve_excludes_memory_expiring_at_current_time(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory expiring now.",
            memory_type=Memory.MemoryType.EVENT,
            expires_at=timezone.now(),
        )

        results = DjangoMemoryRetriever().retrieve(
            MemoryQuery(
                text="current event",
                user_id=self.user.id,
            )
        )

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
            text="Memory",
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
            text="memory",
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

    def test_retrieve_reflects_updated_memory_importance(self):
        first_memory = Memory.objects.create(
            user=self.user,
            content="First memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=2,
        )
        second_memory = Memory.objects.create(
            user=self.user,
            content="Second memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=4,
        )

        MemoryService.update_memory(
            user=self.user,
            memory_id=first_memory.id,
            importance=5,
        )

        results = DjangoMemoryRetriever().retrieve(
            MemoryQuery(
                text="memory",
                user_id=self.user.id,
                limit=2,
            )
        )

        self.assertEqual(results[0].content, "First memory.")
        self.assertEqual(results[0].metadata["importance"], 5)
        self.assertEqual(results[1].content, "Second memory.") 

    def test_retrieve_reflects_updated_memory_expiration(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Temporary memory.",
            memory_type=Memory.MemoryType.EVENT,
            expires_at=timezone.now() + timedelta(days=1),
        )

        retriever = DjangoMemoryRetriever()

        active_results = retriever.retrieve(
            MemoryQuery(
                text="temporary memory",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(active_results), 1)

        MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            expires_at=timezone.now() - timedelta(days=1),
        )

        expired_results = retriever.retrieve(
            MemoryQuery(
                text="temporary memory",
                user_id=self.user.id,
            )
        )

        self.assertEqual(expired_results, [])   

    def test_retrieve_excludes_memory_after_deactivation(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Memory to deactivate.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        retriever = DjangoMemoryRetriever()

        active_results = retriever.retrieve(
            MemoryQuery(
                text="memory to deactivate",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(active_results), 1)

        MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            is_active=False,
        )

        inactive_results = retriever.retrieve(
            MemoryQuery(
                text="memory to deactivate",
                user_id=self.user.id,
            )
        )

        self.assertEqual(inactive_results, [])  

    def test_retrieve_keeps_non_expiring_memory_retrievable_after_update(self):
        memory = Memory.objects.create(
            user=self.user,
            content="Permanent preference memory.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        MemoryService.update_memory(
            user=self.user,
            memory_id=memory.id,
            content="Updated permanent preference memory.",
        )

        results = DjangoMemoryRetriever().retrieve(
            MemoryQuery(
                text="permanent preference",
                user_id=self.user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].content,
            "Updated permanent preference memory.",
        )
        self.assertIsNone(
            Memory.objects.get(id=memory.id).expires_at,
        )    

    def test_retrieve_orders_memories_with_minimum_importance(self):
        low_importance_memory = Memory.objects.create(
            user=self.user,
            content="Low importance memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=1,
        )
        high_importance_memory = Memory.objects.create(
            user=self.user,
            content="High importance memory.",
            memory_type=Memory.MemoryType.FACT,
            importance=5,
        )

        results = DjangoMemoryRetriever().retrieve(
            MemoryQuery(
                text="memory",
                user_id=self.user.id,
                limit=2,
            )
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].content,
            high_importance_memory.content,
        )
        self.assertEqual(
            results[1].content,
            low_importance_memory.content,
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

        response = MemoryDeactivateAPIView.as_view()(
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

        response = MemoryDeactivateAPIView.as_view()(
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
            f"/api/memories/{memory.id}/deactivate/"
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