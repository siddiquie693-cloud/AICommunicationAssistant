from unittest.mock import Mock
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from ai.brain.types import BrainRequest
from ai.context.builder import MemoryContextBuilder
from ai.context.types import Context
from ai.memory.types import MemoryQuery, MemoryResult

from datetime import timedelta
from memory.models import Memory
from memory.retriever import DjangoMemoryRetriever
from ai.memory.service import MemoryEngine


class MemoryContextBuilderTests(TestCase):

    def test_builder_returns_context_with_retrieved_memories(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = [
            MemoryResult(
                content="User prefers concise responses.",
                metadata={
                    "memory_type": "preference",
                    "importance": 5,
                },
            ),
            MemoryResult(
                content="User works with Python.",
                metadata={
                    "memory_type": "fact",
                    "importance": 4,
                },
            ),
        ]

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        request = BrainRequest(
            text="How should you respond to me?",
        )

        context = builder.build(request)

        self.assertIsInstance(context, Context)
        self.assertEqual(
            context.memory,
            [
                {
                    "content": "User prefers concise responses.",
                    "memory_type": "preference",
                    "importance": 5,
                },
                {
                    "content": "User works with Python.",
                    "memory_type": "fact",
                    "importance": 4,
                },
            ],
        )

    def test_builder_retrieves_real_active_memory_for_user(self):

        user = get_user_model().objects.create_user(
            username="contextbuilderintegration",
            email="contextbuilderintegration@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[0]["memory_type"],
            Memory.MemoryType.PREFERENCE,
        )

    def test_builder_does_not_retrieve_other_users_memory(self):
        
        user = get_user_model().objects.create_user(
            username="contextbuilderowner",
            email="contextbuilderowner@example.com",
            password="testpass123",
        )

        other_user = get_user_model().objects.create_user(
            username="contextbuilderother",
            email="contextbuilderother@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=other_user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(context.memory, [])

    def test_builder_prioritizes_owned_memory_over_other_users_matching_memory(self):
        user = get_user_model().objects.create_user(
            username="contextowner",
            email="contextowner@example.com",
            password="testpass123",
        )

        other_user = get_user_model().objects.create_user(
            username="contextother",
            email="contextother@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        Memory.objects.create(
            user=other_user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What concise technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise responses.",
        )    

    def test_builder_does_not_retrieve_inactive_or_expired_memory(self):
        
        user = get_user_model().objects.create_user(
            username="contextbuilderactive",
            email="contextbuilderactive@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            is_active=False,
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise professional responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(context.memory, [])  

    def test_builder_preserves_memory_relevance_order(self):
        user = get_user_model().objects.create_user(
            username="memoryrelevanceorder",
            email="memoryrelevanceorder@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What concise technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 2)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[1]["content"],
            "User prefers concise responses.",
        )    

    def test_builder_orders_conflicting_memories_by_importance(self):
        user = get_user_model().objects.create_user(
            username="conflictimportance",
            email="conflictimportance@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers detailed technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 2)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[0]["importance"],
            5,
        )
        self.assertEqual(
            context.memory[1]["content"],
            "User prefers detailed technical responses.",
        )
        self.assertEqual(
            context.memory[1]["importance"],
            3,
        )  

    def test_builder_orders_equal_importance_conflicting_memories_by_recency(self):
        user = get_user_model().objects.create_user(
            username="conflictrecency",
            email="conflictrecency@example.com",
            password="testpass123",
        )

        older_memory = Memory.objects.create(
            user=user,
            content="User prefers detailed technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        newer_memory = Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        older_memory.created_at = timezone.now() - timedelta(days=1)
        older_memory.save(update_fields=["created_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 2)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[1]["content"],
            "User prefers detailed technical responses.",
        )      

    def test_builder_excludes_expired_conflicting_memory(self):
        user = get_user_model().objects.create_user(
            username="conflictexpired",
            email="conflictexpired@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers detailed technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )    

    def test_builder_excludes_inactive_conflicting_memory(self):
        user = get_user_model().objects.create_user(
            username="conflictinactive",
            email="conflictinactive@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers detailed technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            is_active=False,
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )    

    def test_builder_preserves_deterministic_order_for_equal_memory_metadata(self):
        user = get_user_model().objects.create_user(
            username="conflictdeterministic",
            email="conflictdeterministic@example.com",
            password="testpass123",
        )

        first_memory = Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        second_memory = Memory.objects.create(
            user=user,
            content="User prefers concise professional responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        same_created_at = timezone.now() - timedelta(hours=1)

        Memory.objects.filter(
            id__in=[first_memory.id, second_memory.id]
        ).update(created_at=same_created_at)

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What concise responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 2)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise professional responses.",
        )
        self.assertEqual(
            context.memory[1]["content"],
            "User prefers concise technical responses.",
        )    

    def test_builder_preserves_memory_type_and_importance(self):
        user = get_user_model().objects.create_user(
            username="memorymetadata",
            email="memorymetadata@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["memory_type"],
            Memory.MemoryType.GOAL,
        )
        self.assertEqual(
            context.memory[0]["importance"],
            5,
        )  

    def test_builder_retrieves_updated_memory_content(self):
        user = get_user_model().objects.create_user(
            username="updatedcontent",
            email="updatedcontent@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User prefers detailed responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        memory.content = "User prefers concise technical responses."
        memory.save(update_fields=["content", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        ) 

    def test_builder_reflects_updated_memory_type(self):
        user = get_user_model().objects.create_user(
            username="updatedtype",
            email="updatedtype@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory.memory_type = Memory.MemoryType.TASK
        memory.save(update_fields=["memory_type", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["memory_type"],
            Memory.MemoryType.TASK,
        )

    def test_builder_reflects_updated_memory_importance(self):
        user = get_user_model().objects.create_user(
            username="updatedimportance",
            email="updatedimportance@example.com",
            password="testpass123",
        )

        first_memory = Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=2,
        )

        second_memory = Memory.objects.create(
            user=user,
            content="User prefers detailed technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=3,
        )

        first_memory.importance = 5
        first_memory.save(update_fields=["importance", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What technical responses does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 2)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[0]["importance"],
            5,
        )   

    def test_builder_excludes_memory_after_updated_expiration(self):
        user = get_user_model().objects.create_user(
            username="updatedexpiration",
            email="updatedexpiration@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory.expires_at = timezone.now() - timedelta(minutes=1)
        memory.save(update_fields=["expires_at", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, []) 

    def test_builder_excludes_memory_after_deactivation(self):
        user = get_user_model().objects.create_user(
            username="updateddeactivation",
            email="updateddeactivation@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory.is_active = False
        memory.save(update_fields=["is_active", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, []) 

    def test_builder_retrieves_memory_after_reactivation(self):
        user = get_user_model().objects.create_user(
            username="reactivatedmemory",
            email="reactivatedmemory@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
            is_active=False,
        )

        memory.is_active = True
        memory.save(update_fields=["is_active", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User is preparing for a Python backend interview.",
        )         

    def test_builder_preserves_updated_memory_metadata(self):
        user = get_user_model().objects.create_user(
            username="updatedmetadata",
            email="updatedmetadata@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=3,
            metadata={"source": "initial"},
        )

        memory.importance = 5
        memory.metadata = {
            "source": "updated",
            "category": "career",
        }
        memory.save(update_fields=["importance", "metadata", "updated_at"])

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["importance"],
            5,
        )
        self.assertEqual(
            context.memory[0]["source"],
            "updated",
        )
        self.assertEqual(
            context.memory[0]["category"],
            "career",
        )   

    def test_builder_reflects_latest_memory_state_after_multiple_updates(self):
        user = get_user_model().objects.create_user(
            username="multipleupdates",
            email="multipleupdates@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=3,
            metadata={"stage": "initial"},
        )

        memory.content = "User is preparing for a Python backend interview."
        memory.importance = 5
        memory.metadata = {
            "stage": "final",
            "domain": "backend",
        }
        memory.save(
            update_fields=[
                "content",
                "importance",
                "metadata",
                "updated_at",
            ]
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User is preparing for a Python backend interview.",
        )
        self.assertEqual(
            context.memory[0]["importance"],
            5,
        )
        self.assertEqual(
            context.memory[0]["stage"],
            "final",
        )
        self.assertEqual(
            context.memory[0]["domain"],
            "backend",
        )             

    def test_builder_excludes_deleted_memory(self):
        user = get_user_model().objects.create_user(
            username="deletedmemory",
            email="deletedmemory@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory.delete()

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, [])  

    def test_builder_does_not_retrieve_deleted_memory_after_recreation(self):
        user = get_user_model().objects.create_user(
            username="deletedrecreated",
            email="deletedrecreated@example.com",
            password="testpass123",
        )

        old_memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        old_memory.delete()

        Memory.objects.create(
            user=user,
            content="User is preparing for a data analysis interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=4,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User is preparing for a data analysis interview.",
        )     

    def test_builder_keeps_other_memory_after_deleting_one_memory(self):
        user = get_user_model().objects.create_user(
            username="deleteonememory",
            email="deleteonememory@example.com",
            password="testpass123",
        )

        deleted_memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        retained_memory = Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=4,
        )

        deleted_memory.delete()

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What does the user prefer?",
        )

        context = builder.build(request)

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            retained_memory.content,
        )
        self.assertEqual(
            context.memory[0]["memory_type"],
            Memory.MemoryType.PREFERENCE,
        ) 

    def test_builder_does_not_preserve_deleted_memory_metadata(self):
        user = get_user_model().objects.create_user(
            username="deletedmetadata",
            email="deletedmetadata@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
            metadata={
                "source": "deleted",
                "category": "career",
            },
        )

        memory.delete()

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, []) 

    def test_builder_keeps_other_users_memory_when_owned_memory_is_deleted(self):
        user = get_user_model().objects.create_user(
            username="deletedownedmemory",
            email="deletedownedmemory@example.com",
            password="testpass123",
        )

        other_user = get_user_model().objects.create_user(
            username="otherretainedmemory",
            email="otherretainedmemory@example.com",
            password="testpass123",
        )

        owned_memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        Memory.objects.create(
            user=other_user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=3,
        )

        owned_memory.delete()

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, [])

    def test_builder_returns_empty_context_when_all_matching_memories_are_deleted(self):
        user = get_user_model().objects.create_user(
            username="deleteallmatching",
            email="deleteallmatching@example.com",
            password="testpass123",
        )

        first_memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        second_memory = Memory.objects.create(
            user=user,
            content="User is preparing for a data analysis interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=4,
        )

        first_memory.delete()
        second_memory.delete()

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, [])  

    def test_builder_does_not_return_deleted_memory_after_multiple_context_builds(self):
        user = get_user_model().objects.create_user(
            username="multiplecontextdelete",
            email="multiplecontextdelete@example.com",
            password="testpass123",
        )

        memory = Memory.objects.create(
            user=user,
            content="User is preparing for a Python backend interview.",
            memory_type=Memory.MemoryType.GOAL,
            importance=5,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        request = BrainRequest(
            text="What is the user preparing for?",
        )

        first_context = builder.build(request)

        memory.delete()

        second_context = builder.build(request)

        self.assertEqual(len(first_context.memory), 1)
        self.assertEqual(second_context.memory, [])                      

    def test_builder_passes_request_text_and_user_id_to_memory_engine(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = []

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=42,
        )

        request = BrainRequest(
            text="What are my preferences?",
        )

        builder.build(request)

        memory_engine.retrieve.assert_called_once_with(
            MemoryQuery(
                text="What are my preferences?",
                user_id=42,
            )
        )

    def test_builder_preserves_memory_result_metadata(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = [
            MemoryResult(
                content="User prefers English.",
                metadata={
                    "memory_id": 12,
                    "memory_type": "preference",
                    "importance": 5,
                    "source": "explicit",
                },
            ),
        ]

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=9,
        )

        request = BrainRequest(
            text="What language do I prefer?",
        )

        context = builder.build(request)

        self.assertEqual(
            context.memory[0],
            {
                "content": "User prefers English.",
                "memory_id": 12,
                "memory_type": "preference",
                "importance": 5,
                "source": "explicit",
            },
        )

    def test_builder_rejects_non_brain_request(self):
        memory_engine = Mock()

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        with self.assertRaises(TypeError):
            builder.build("What are my preferences?")

        memory_engine.retrieve.assert_not_called()

    def test_builder_returns_empty_memory_when_memory_engine_returns_no_results(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = []

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        request = BrainRequest(
            text="What do you remember about me?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, [])
        self.assertIsInstance(context, Context)