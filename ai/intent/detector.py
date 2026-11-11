from abc import ABC, abstractmethod

from ai.brain.types import BrainRequest
from ai.intent.types import Intent


class IntentDetector(ABC):
    """
    Contract for implementations that detect user intent.
    """

    @abstractmethod
    def detect(
        self,
        request: BrainRequest,
        *,
        context=None,
    ) -> Intent:
        """
        Detect and return a structured Intent from a BrainRequest.
        """
        raise NotImplementedError

class BasicIntentDetector(IntentDetector):
    """
    Deterministic natural-language intent detector.

    Supports multiple clear phrasings for common user requests.
    """

    CALL_PREFIXES = (
        "call ",
        "phone ",
        "ring ",
        "dial ",
    )

    REQUEST_PREFIXES = (
        "can you ",
        "could you ",
        "please ",
        "would you ",
        "will you ",
    )

    MESSAGE_PREFIXES = (
        "send ",
        "message ",
        "text ",
    )

    APP_PREFIXES = (
        "open ",
        "start ",
        "launch ",
    )

    REMINDER_PREFIXES = (
        "remind me",
        "set a reminder",
        "create a reminder",
    )

    NAVIGATION_PREFIXES = (
        "navigate ",
        "go to ",
        "take me to ",
        "directions to ",
    )

    MEDIA_PREFIXES = (
        "play ",
        "play music",
        "play song",
    )

    CONVERSATION_PHRASES = {
        "hello",
        "hi",
        "hey",
        "hi nira",
        "hello nira",
        "good morning",
        "good afternoon",
        "good evening",
        "thanks",
        "thank you",
        "thanks nira",
        "thank you nira",
        "how are you",
        "how are you?",
    }

    def detect(
        self,
        request: BrainRequest,
        *,
        context=None,
    ) -> Intent:
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        text = request.text.strip()
        normalized_text = text.lower()

        command_text = self._remove_request_prefix(
            text,
            normalized_text,
        )

        if command_text != text:
            text = command_text
            normalized_text = text.lower()

        if normalized_text in self.CONVERSATION_PHRASES:
            return Intent(
                name="unknown",
                parameters={},
            )

        if normalized_text.startswith(self.CALL_PREFIXES):
            recipient = self._remove_prefix(
                text,
                normalized_text,
                self.CALL_PREFIXES,
            )

            if recipient:
                return Intent(
                    name="call_person",
                    parameters={"recipient": recipient},
                )

        if normalized_text.startswith(self.MESSAGE_PREFIXES):
            content = self._remove_prefix(
                text,
                normalized_text,
                self.MESSAGE_PREFIXES,
            )

            if content:
                recipient, contextual_content = (
                    self._resolve_contextual_message_request(
                        content,
                        context,
                    )
                )

                explicit_message = self._extract_explicit_message_request(
                    content,
                )
                if explicit_message:
                    recipient, message_content = explicit_message
                    return Intent(
                        name="send_message",
                        parameters={
                            "recipient": recipient,
                            "request": message_content,
                        },
                    )
                if recipient:
                    return Intent(
                        name="send_message",
                        parameters={
                            "recipient": recipient,
                            "request": contextual_content,
                        },
                    )
                return Intent(
                    name="send_message",
                    parameters={"request": contextual_content},
                )

        if normalized_text.startswith(self.APP_PREFIXES):
            app = self._remove_prefix(
                text,
                normalized_text,
                self.APP_PREFIXES,
            )

            if app:
                return Intent(
                    name="open_app",
                    parameters={"app": app},
                )

        if normalized_text.startswith(self.REMINDER_PREFIXES):
            reminder_details = self._remove_prefix(
                text,
                normalized_text,
                self.REMINDER_PREFIXES,
            ).strip()

            if reminder_details:
                return Intent(
                    name="create_reminder",
                    parameters={"request": text},
                )

        if normalized_text.startswith(self.NAVIGATION_PREFIXES):
            location = self._remove_prefix(
                text,
                normalized_text,
                self.NAVIGATION_PREFIXES,
            ).strip()

            if location.lower() == "to":
                location = ""
            elif location.lower().startswith("to "):
                location = location[3:].strip()

            if location:
                return Intent(
                    name="navigate",
                    parameters={"location": location},
                )

        if normalized_text.startswith(self.MEDIA_PREFIXES):
            return Intent(
                name="play_media",
                parameters={"request": text},
            )

        if self._is_notification_request(normalized_text):
            return Intent(
                name="check_notifications",
                parameters={},
            )

        return Intent(
            name="unknown",
            parameters={},
        )

    @staticmethod
    def _remove_prefix(
        text: str,
        normalized_text: str,
        prefixes: tuple[str, ...],
    ) -> str:
        for prefix in prefixes:
            if normalized_text.startswith(prefix):
                return text[len(prefix):].strip()

        return ""

    @staticmethod
    def _is_notification_request(normalized_text: str) -> bool:
        return (
            normalized_text in {
                "show notifications",
                "check notifications",
                "check my notifications",
                "show my notifications",
            }
        )

    @classmethod
    def _remove_request_prefix(
        cls,
        text: str,
        normalized_text: str,
    ) -> str:
        for prefix in cls.REQUEST_PREFIXES:
            if normalized_text.startswith(prefix):
                return text[len(prefix):].strip()

        return text

    @staticmethod
    def _resolve_conversational_recipient(context) -> str | None:
        if context is None:
            return None

        conversation = getattr(context, "conversation", None)

        if not conversation:
            return None

        for message in reversed(conversation):
            content = message.get("content", "")

            if not isinstance(content, str):
                continue

            normalized_content = content.strip()

            for prefix in (
                "call ",
                "phone ",
                "ring ",
                "dial ",
                "calling ",
            ):
                if normalized_content.lower().startswith(prefix):
                    recipient = normalized_content[len(prefix):].strip()

                    if recipient:
                        if recipient.endswith("."):
                            recipient = recipient[:-1].strip()

                        return recipient

        return None

    @staticmethod
    def _extract_explicit_message_request(
        text: str,
    ) -> tuple[str, str] | None:
        message_text = text.strip()
        normalized_text = message_text.casefold()

        prefix = "a message to "
        if not normalized_text.startswith(prefix):
            return None

        remainder = message_text[len(prefix):].strip()
        normalized_remainder = remainder.casefold()

        marker = " saying "
        marker_index = normalized_remainder.find(marker)

        if marker_index == -1:
            return None

        recipient = remainder[:marker_index].strip()
        request = remainder[marker_index + len(marker):].strip()

        if not recipient or not request:
            return None

        return recipient, request

    @classmethod
    def _resolve_contextual_message_request(
        cls,
        text: str,
        context,
    ) -> tuple[str | None, str]:
        message_text = text.strip()
        normalized_message_text = message_text.lower()

        # Explicitly resolved person takes precedence.
        person = getattr(context, "person", None)
        person_name = None

        if isinstance(person, dict):
            name = person.get("name")
            if isinstance(name, str) and name.strip():
                person_name = name.strip()

        relationship_prefixes = (
            "my manager ",
            "my colleague ",
            "my friend ",
            "my family member ",
        )

        relationship_request = None
        for prefix in relationship_prefixes:
            if normalized_message_text.startswith(prefix):
                relationship_request = message_text[len(prefix):].strip()
                break

        if relationship_request is not None:
            if person_name:
                return person_name, relationship_request

            relationship = prefix.strip().removeprefix("my ")
            memories = getattr(context, "memory", None) or []
            candidates = []

            for memory in memories:
                if not isinstance(memory, dict):
                    continue

                name = memory.get("person_name")
                memory_relationship = memory.get("relationship")

                if (
                    isinstance(name, str)
                    and name.strip()
                    and isinstance(memory_relationship, str)
                    and memory_relationship.strip().casefold()
                    == relationship.casefold()
                ):
                    candidates.append(name.strip())

            unique_candidates = {
                name.casefold(): name
                for name in candidates
            }

            if len(unique_candidates) == 1 and relationship_request:
                return next(iter(unique_candidates.values())), relationship_request

            return None, message_text

        for pronoun in ("him", "her", "them"):
            pronoun_prefix = f"{pronoun} "

            if not normalized_message_text.startswith(pronoun_prefix):
                continue

            request = message_text[len(pronoun_prefix):].strip()

            if not request:
                return None, message_text

            memories = getattr(context, "memory", None) or []
            candidates = []

            for memory in memories:
                if not isinstance(memory, dict):
                    continue

                name = memory.get("person_name")
                if isinstance(name, str) and name.strip():
                    candidates.append(name.strip())

            unique_candidates = {
                name.casefold(): name
                for name in candidates
            }

            # Memory conflicts only when it identifies a different person
            # as the same unresolved pronoun's likely referent.
            if person_name:
                conflicting_candidates = {
                    memory["person_name"].strip().casefold()
                    for memory in memories
                    if isinstance(memory, dict)
                    and isinstance(memory.get("person_name"), str)
                    and memory["person_name"].strip()
                    and isinstance(memory.get("relationship"), str)
                    and memory["relationship"].strip().casefold()
                    == "friend"
                }

                if (
                    conflicting_candidates
                    and person_name.casefold() not in conflicting_candidates
                ):
                    return None, message_text

                return person_name, request

            conversation_recipient = (
                cls._resolve_conversational_recipient(context)
            )

            if conversation_recipient:
                if (
                    unique_candidates
                    and conversation_recipient.casefold()
                    not in unique_candidates
                ):
                    return None, message_text

                if (
                    not unique_candidates
                    or conversation_recipient.casefold() in unique_candidates
                ):
                    return conversation_recipient, request

            if len(unique_candidates) == 1:
                return next(iter(unique_candidates.values())), request

            return None, message_text

        return None, message_text
