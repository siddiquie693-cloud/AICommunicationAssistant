from ai.brain.types import BrainRequest
from ai.context.conversation import ConversationContextBuilder
from ai.context.types import Context
from ai.memory.service import MemoryEngine
from ai.memory.types import MemoryQuery
from conversations.models import Conversation

class MemoryContextBuilder:
    """
    Builds personal-memory and person context for a NIRA Brain request.

    Memory and person context sources are injected so this builder
    remains independent from storage and identity-resolution details.
    """

    def __init__(
        self,
        memory_engine: MemoryEngine,
        user_id: int | None = None,
        user=None,
        person_context_service=None,
        conversation_context_builder=None,
    ):
        if user is None and user_id is None:
            raise ValueError(
                "Either user or user_id must be provided."
            )

        self.memory_engine = memory_engine
        self.user = user
        self.user_id = user.id if user is not None else user_id
        self.person_context_service = person_context_service
        self.conversation_context_builder = (
            conversation_context_builder
            or ConversationContextBuilder()
        )

    def build(
        self,
        request: BrainRequest,
        *,
        person=None,
        conversation=None,
    ) -> Context:
        """
        Build Context using relevant personal memory,
        person context, and conversation history.
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        results = self.memory_engine.retrieve(
            MemoryQuery(
                text=request.text,
                user_id=self.user_id,
            )
        )

        memory = [
            {
                "content": result.content,
                **result.metadata,
            }
            for result in results
        ]

        person_context = None

        if person is not None:
            if self.user is None:
                raise ValueError(
                    "A user instance is required for person context."
                )

            if person.user_id != self.user.id:
                raise ValueError(
                    "Person must belong to the same user "
                    "as the context owner."
                )

            if self.person_context_service is None:
                raise ValueError(
                    "Person Context Service is not configured."
                )

            person_context = self.person_context_service.build(
                user=self.user,
                person=person,
            )

        conversation_context = []

        if conversation is not None:
            if self.user is None:
                raise ValueError(
                    "A user instance is required for conversation context."
                )

            if conversation.user_id != self.user.id:
                raise ValueError(
                    "Conversation must belong to the same user "
                    "as the context owner."
                )

            if person is not None and conversation.person_id != person.id:
                raise ValueError(
                    "Conversation must belong to the resolved person."
                )

            conversation_context = self.conversation_context_builder.build(
                conversation,
            )

        return Context(
            memory=memory,
            person=person_context,
            conversation=conversation_context,
        )