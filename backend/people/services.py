import re
from django.db.models import Q
from django.utils import timezone

from memory.models import Memory
from .models import Person


class PersonIdentityResolver:
    """Resolves a user's Person record from contact identifiers."""

    @staticmethod
    def _normalize_phone_number(phone_number):
        if not phone_number:
            return ""

        return re.sub(r"[\s\-()]", "", phone_number.strip())

    @staticmethod
    def _normalize_email(email):
        if not email:
            return ""

        return email.strip().lower()

    @staticmethod
    def resolve(*, user, phone_number=None, email=None, name=None):
        identifiers = [
            identifier
            for identifier in (phone_number, email, name)
            if identifier
        ]

        if not identifiers:
            return None

        matches = []

        if phone_number:
            phone_match = PersonIdentityResolver.resolve_by_phone(
                user=user,
                phone_number=phone_number,
            )
            if phone_match is not None:
                matches.append(phone_match)

        if email:
            email_match = PersonIdentityResolver.resolve_by_email(
                user=user,
                email=email,
            )
            if email_match is not None:
                matches.append(email_match)

        if name:
            name_match = PersonIdentityResolver.resolve_by_name(
                user=user,
                name=name,
            )
            if name_match is not None:
                matches.append(name_match)

        unique_matches = {person.id: person for person in matches}

        if len(unique_matches) != 1:
            return None

        return next(iter(unique_matches.values()))

    @staticmethod
    def resolve_by_phone(*, user, phone_number):
        normalized_phone = PersonIdentityResolver._normalize_phone_number(
            phone_number
        )

        if not normalized_phone:
            return None

        matches = [
            person
            for person in Person.objects.filter(
                user=user,
                is_active=True,
            )
            if PersonIdentityResolver._normalize_phone_number(
                person.phone_number
            )
            == normalized_phone
        ]

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def resolve_by_email(*, user, email):
        normalized_email = PersonIdentityResolver._normalize_email(email)

        if not normalized_email:
            return None

        matches = [
            person
            for person in Person.objects.filter(
                user=user,
                is_active=True,
            )
            if PersonIdentityResolver._normalize_email(person.email)
            == normalized_email
        ]

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def resolve_by_name(*, user, name):
        if not name:
            return None

        return Person.objects.filter(
            user=user,
            name__iexact=name.strip(),
            is_active=True,
        ).first()

class PersonContextService:
    """Builds structured, user-owned context for an identified Person."""

    @staticmethod
    def build(*, user, person, memory_limit=None):
        if not isinstance(person, Person):
            raise ValueError("person must be a Person instance.")

        if person.user_id != user.id:
            raise ValueError(
                "Person must belong to the same user as the context owner."
            )

        if not person.is_active:
            return None

        now = timezone.now()

        memories = Memory.objects.filter(
            user=user,
            person=person,
            is_active=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).order_by("-created_at", "-id")

        if memory_limit is not None:
            memories = memories[:memory_limit]

        return {
            "id": person.id,
            "name": person.name,
            "phone_number": person.phone_number,
            "email": person.email,
            "relationship": person.relationship,
            "notes": person.notes,
            "metadata": person.metadata,
            "memories": [
                {
                    "memory_id": memory.id,
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "importance": memory.importance,
                    "metadata": memory.metadata,
                }
                for memory in memories
            ],
        }    