from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from .services import PersonIdentityResolver, PersonContextService
from .models import Person
from datetime import timedelta

from django.utils import timezone
from memory.models import Memory


class PersonModelTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="personmodeluser",
            email="personmodeluser@example.com",
            password="testpass123",
        )

    def test_person_belongs_to_user(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        self.assertEqual(person.user, self.user)

    def test_person_has_expected_default_values(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.OTHER,
        )
        self.assertEqual(person.phone_number, "")
        self.assertEqual(person.email, "")
        self.assertEqual(person.notes, "")
        self.assertEqual(person.metadata, {})
        self.assertTrue(person.is_active)

    def test_person_accepts_contact_information(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
            phone_number="+919876543210",
            email="rahul@example.com",
        )

        self.assertEqual(person.name, "Rahul Sharma")
        self.assertEqual(person.phone_number, "+919876543210")
        self.assertEqual(person.email, "rahul@example.com")

    def test_person_accepts_relationship_types(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            relationship=Person.RelationshipType.FRIEND,
        )

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.FRIEND,
        )

    def test_person_accepts_notes_and_metadata(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            notes="Works with the user on backend projects.",
            metadata={
                "source": "manual",
                "preferred_contact": "whatsapp",
            },
        )

        self.assertEqual(
            person.notes,
            "Works with the user on backend projects.",
        )
        self.assertEqual(
            person.metadata["source"],
            "manual",
        )

    def test_person_can_be_deactivated(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            is_active=False,
        )

        self.assertFalse(person.is_active)

    def test_person_requires_a_name(self):
        person = Person(
            user=self.user,
            name="",
        )

        with self.assertRaises(ValidationError):
            person.full_clean()

    def test_person_rejects_invalid_email(self):
        person = Person(
            user=self.user,
            name="Rahul",
            email="not-an-email",
        )

        with self.assertRaises(ValidationError):
            person.full_clean()

    def test_person_str_returns_name(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        self.assertEqual(str(person), "Rahul Sharma")

    def test_person_allows_multiple_people_for_same_user(self):
        first_person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )
        second_person = Person.objects.create(
            user=self.user,
            name="Priya",
        )

        self.assertEqual(
            Person.objects.filter(user=self.user).count(),
            2,
        )
        self.assertNotEqual(first_person.id, second_person.id)

    def test_person_data_is_isolated_by_user(self):
        other_user = get_user_model().objects.create_user(
            username="otherpersonuser",
            email="otherpersonuser@example.com",
            password="testpass123",
        )

        Person.objects.create(
            user=self.user,
            name="Rahul",
        )
        Person.objects.create(
            user=other_user,
            name="Rahul",
        )

        self.assertEqual(
            Person.objects.filter(user=self.user).count(),
            1,
        )
        self.assertEqual(
            Person.objects.filter(user=other_user).count(),
            1,
        )

    def test_person_relationship_choices_are_defined(self):
        relationship_values = {
            choice.value
            for choice in Person.RelationshipType
        }

        self.assertEqual(
            relationship_values,
            {
                "family",
                "friend",
                "colleague",
                "manager",
                "client",
                "other",
            },
        )

    def test_person_relationship_defaults_to_other(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
        )

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.OTHER,
        )

    def test_person_relationship_can_be_changed(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            relationship=Person.RelationshipType.FRIEND,
        )

        person.relationship = Person.RelationshipType.COLLEAGUE
        person.full_clean()
        person.save()

        person.refresh_from_db()

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.COLLEAGUE,
        ) 

    def test_person_model_regression_preserves_user_ownership(self):
        person = Person.objects.create(
            user=self.user,
            name="Regression Person",
        )

        self.assertEqual(person.user_id, self.user.id)

        person.refresh_from_db()

        self.assertEqual(person.user_id, self.user.id)


    def test_person_model_regression_preserves_contact_fields(self):
        person = Person.objects.create(
            user=self.user,
            name="Contact Regression",
            phone_number="+919876543210",
            email="contact.regression@example.com",
        )

        person.refresh_from_db()

        self.assertEqual(person.name, "Contact Regression")
        self.assertEqual(person.phone_number, "+919876543210")
        self.assertEqual(
            person.email,
            "contact.regression@example.com",
        )


    def test_person_model_regression_preserves_default_state(self):
        person = Person.objects.create(
            user=self.user,
            name="Default Regression",
        )

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.OTHER,
        )
        self.assertTrue(person.is_active)
        self.assertEqual(person.notes, "")
        self.assertEqual(person.metadata, {})  

    def test_person_relationship_regression_supports_all_defined_choices(self):
        expected_relationships = {
            Person.RelationshipType.FAMILY,
            Person.RelationshipType.FRIEND,
            Person.RelationshipType.COLLEAGUE,
            Person.RelationshipType.MANAGER,
            Person.RelationshipType.CLIENT,
            Person.RelationshipType.OTHER,
        }

        actual_relationships = {
            value
            for value, _ in Person.RelationshipType.choices
        }

        self.assertEqual(actual_relationships, expected_relationships)


    def test_person_relationship_regression_persists_each_relationship(self):
        relationships = [
            Person.RelationshipType.FAMILY,
            Person.RelationshipType.FRIEND,
            Person.RelationshipType.COLLEAGUE,
            Person.RelationshipType.MANAGER,
            Person.RelationshipType.CLIENT,
            Person.RelationshipType.OTHER,
        ]

        for index, relationship in enumerate(relationships):
            person = Person.objects.create(
                user=self.user,
                name=f"Relationship Regression {index}",
                relationship=relationship,
            )

            person.refresh_from_db()

            self.assertEqual(person.relationship, relationship)


    def test_person_relationship_regression_preserves_existing_relationship_on_update(self):
        person = Person.objects.create(
            user=self.user,
            name="Relationship Update Regression",
            relationship=Person.RelationshipType.FRIEND,
        )

        person.notes = "Relationship regression update"
        person.save(update_fields=["notes"])

        person.refresh_from_db()

        self.assertEqual(
            person.relationship,
            Person.RelationshipType.FRIEND,
        )
        self.assertEqual(
            person.notes,
            "Relationship regression update",
        )      

    def test_identity_resolution_regression_requires_unique_phone_match(self):
        person_one = Person.objects.create(
            user=self.user,
            name="Phone Match One",
            phone_number="+919876543210",
        )
        Person.objects.create(
            user=self.user,
            name="Phone Match Two",
            phone_number="+919876543210",
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number=person_one.phone_number,
        )

        self.assertIsNone(resolved)


    def test_identity_resolution_regression_requires_unique_email_match(self):
        Person.objects.create(
            user=self.user,
            name="Email Match One",
            email="duplicate@example.com",
        )
        Person.objects.create(
            user=self.user,
            name="Email Match Two",
            email="duplicate@example.com",
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="duplicate@example.com",
        )

        self.assertIsNone(resolved)


    def test_identity_resolution_regression_does_not_mix_different_identifiers(self):
        phone_person = Person.objects.create(
            user=self.user,
            name="Phone Person",
            phone_number="+919876543210",
        )
        email_person = Person.objects.create(
            user=self.user,
            name="Email Person",
            email="emailperson@example.com",
        )

        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            phone_number=phone_person.phone_number,
            email=email_person.email,
        )

        self.assertIsNone(resolved) 

    def test_person_memory_regression_preserves_active_person_memory(self):
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Memory Regression Person",
        )

        memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Important person memory",
            memory_type="fact",
            is_active=True,
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(len(context["memories"]), 1)
        self.assertEqual(
            context["memories"][0]["memory_id"],
            memory.id,
        )
        self.assertEqual(
            context["memories"][0]["content"],
            "Important person memory",
        )


    def test_person_memory_regression_excludes_inactive_person_memory(self):

        person = Person.objects.create(
            user=self.user,
            name="Inactive Memory Regression",
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Inactive person memory",
            memory_type="fact",
            is_active=False,
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(context["memories"], [])

    def test_person_memory_regression_excludes_expired_person_memory(self):
        
        person = Person.objects.create(
            user=self.user,
            name="Expired Memory Regression",
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Expired person memory",
            memory_type="fact",
            is_active=True,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(context["memories"], [])   

    def test_person_context_regression_returns_complete_person_identity(self):
        person = Person.objects.create(
            user=self.user,
            name="Context Regression Person",
            phone_number="+919876543210",
            email="context.regression@example.com",
            relationship=Person.RelationshipType.COLLEAGUE,
            notes="Important context notes",
            metadata={"team": "engineering"},
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(context["id"], person.id)
        self.assertEqual(context["name"], "Context Regression Person")
        self.assertEqual(context["phone_number"], "+919876543210")
        self.assertEqual(
            context["email"],
            "context.regression@example.com",
        )
        self.assertEqual(
            context["relationship"],
            Person.RelationshipType.COLLEAGUE,
        )
        self.assertEqual(context["notes"], "Important context notes")
        self.assertEqual(
            context["metadata"],
            {"team": "engineering"},
        )


    def test_person_context_regression_respects_memory_limit(self):
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Context Limit Regression",
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Memory one",
            memory_type="fact",
        )
        Memory.objects.create(
            user=self.user,
            person=person,
            content="Memory two",
            memory_type="fact",
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
            memory_limit=1,
        )

        self.assertEqual(len(context["memories"]), 1)

    def test_person_context_regression_returns_none_for_inactive_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Inactive Context Regression",
            is_active=False,
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertIsNone(context)        

    def test_resolve_by_phone_returns_owned_active_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="+919876543210",
        )

        self.assertEqual(resolved, person)

    def test_resolve_by_phone_does_not_return_other_users_person(self):
        other_user = get_user_model().objects.create_user(
            username="otherphoneuser",
            email="otherphoneuser@example.com",
            password="testpass123",
        )

        Person.objects.create(
            user=other_user,
            name="Rahul",
            phone_number="+919876543210",
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="+919876543210",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_phone_does_not_return_inactive_person(self):
        Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
            is_active=False,
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="+919876543210",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_email_returns_owned_active_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            email="rahul@example.com",
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="rahul@example.com",
        )

        self.assertEqual(resolved, person)

    def test_resolve_by_email_does_not_return_other_users_person(self):
        other_user = get_user_model().objects.create_user(
            username="otheremailuser",
            email="otheremailuser@example.com",
            password="testpass123",
        )

        Person.objects.create(
            user=other_user,
            name="Rahul",
            email="rahul@example.com",
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="rahul@example.com",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_email_does_not_return_inactive_person(self):
        Person.objects.create(
            user=self.user,
            name="Rahul",
            email="rahul@example.com",
            is_active=False,
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="rahul@example.com",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_name_is_case_insensitive(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        resolved = PersonIdentityResolver.resolve_by_name(
            user=self.user,
            name="rahul sharma",
        )

        self.assertEqual(resolved, person)

    def test_resolve_by_name_strips_whitespace(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        resolved = PersonIdentityResolver.resolve_by_name(
            user=self.user,
            name="  Rahul Sharma  ",
        )

        self.assertEqual(resolved, person)

    def test_resolve_by_name_does_not_return_other_users_person(self):
        other_user = get_user_model().objects.create_user(
            username="othernameuser",
            email="othernameuser@example.com",
            password="testpass123",
        )

        Person.objects.create(
            user=other_user,
            name="Rahul Sharma",
        )

        resolved = PersonIdentityResolver.resolve_by_name(
            user=self.user,
            name="Rahul Sharma",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_name_does_not_return_inactive_person(self):
        Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
            is_active=False,
        )

        resolved = PersonIdentityResolver.resolve_by_name(
            user=self.user,
            name="Rahul Sharma",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_phone_returns_none_for_empty_phone_number(self):
        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_email_returns_none_for_empty_email(self):
        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_name_returns_none_for_empty_name(self):
        resolved = PersonIdentityResolver.resolve_by_name(
            user=self.user,
            name="   ",
        )

        self.assertIsNone(resolved) 

    def test_resolve_by_phone_normalizes_common_formatting(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="+91 98765-43210",
        )

        self.assertEqual(resolved, person)

    def test_resolve_by_email_normalizes_whitespace_and_case(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            email="rahul@example.com",
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="  RAHUL@EXAMPLE.COM  ",
        )

        self.assertEqual(resolved, person) 

    def test_resolve_by_phone_returns_none_when_multiple_active_people_match(self):
        Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
        )
        Person.objects.create(
            user=self.user,
            name="Amit",
            phone_number="+91 98765-43210",
        )

        resolved = PersonIdentityResolver.resolve_by_phone(
            user=self.user,
            phone_number="+919876543210",
        )

        self.assertIsNone(resolved)

    def test_resolve_by_email_returns_none_when_multiple_active_people_match(self):
        Person.objects.create(
            user=self.user,
            name="Rahul",
            email="rahul@example.com",
        )
        Person.objects.create(
            user=self.user,
            name="Amit",
            email=" RAHUL@EXAMPLE.COM ",
        )

        resolved = PersonIdentityResolver.resolve_by_email(
            user=self.user,
            email="rahul@example.com",
        )

        self.assertIsNone(resolved)   

    def test_resolve_returns_person_by_phone(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
        )

        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            phone_number="+91 98765-43210",
        )

        self.assertEqual(resolved, person)

    def test_resolve_returns_person_by_email(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul",
            email="rahul@example.com",
        )

        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            email="RAHUL@EXAMPLE.COM",
        )

        self.assertEqual(resolved, person)

    def test_resolve_returns_person_by_name(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            name="  rahul sharma  ",
        )

        self.assertEqual(resolved, person)

    def test_resolve_returns_none_when_no_identifier_matches(self):
        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            phone_number="+919876543210",
            email="unknown@example.com",
            name="Unknown Person",
        )

        self.assertIsNone(resolved) 

    def test_resolve_returns_none_when_identifiers_match_different_people(self):
        phone_person = Person.objects.create(
            user=self.user,
            name="Rahul",
            phone_number="+919876543210",
        )
        email_person = Person.objects.create(
            user=self.user,
            name="Amit",
            email="amit@example.com",
        )

        resolved = PersonIdentityResolver.resolve(
            user=self.user,
            phone_number="+919876543210",
            email="amit@example.com",
        )

        self.assertIsNone(resolved)
        self.assertNotEqual(phone_person.id, email_person.id) 

    def test_build_person_context_returns_person_data(self):
        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
            phone_number="+919876543210",
            email="rahul@example.com",
            relationship=Person.RelationshipType.FRIEND,
            notes="Backend developer",
            metadata={"preferred_contact": "whatsapp"},
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(context["id"], person.id)
        self.assertEqual(context["name"], "Rahul Sharma")
        self.assertEqual(context["phone_number"], "+919876543210")
        self.assertEqual(context["email"], "rahul@example.com")
        self.assertEqual(
            context["relationship"],
            Person.RelationshipType.FRIEND,
        )
        self.assertEqual(context["notes"], "Backend developer")
        self.assertEqual(
            context["metadata"]["preferred_contact"],
            "whatsapp",
        )
        self.assertEqual(context["memories"], [])

    def test_build_person_context_includes_active_person_memories(self):
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Rahul prefers concise technical discussions.",
            memory_type=Memory.MemoryType.PREFERENCE,
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(len(context["memories"]), 1)
        self.assertEqual(
            context["memories"][0]["memory_id"],
            memory.id,
        )
        self.assertEqual(
            context["memories"][0]["content"],
            "Rahul prefers concise technical discussions.",
        )

    def test_build_person_context_excludes_inactive_and_expired_memories(self):
        from datetime import timedelta

        from django.utils import timezone
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Rahul Sharma",
        )

        active_memory = Memory.objects.create(
            user=self.user,
            person=person,
            content="Active memory",
            memory_type=Memory.MemoryType.FACT,
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Inactive memory",
            memory_type=Memory.MemoryType.FACT,
            is_active=False,
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Expired memory",
            memory_type=Memory.MemoryType.FACT,
            expires_at=timezone.now() - timedelta(days=1),
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(len(context["memories"]), 1)
        self.assertEqual(
            context["memories"][0]["memory_id"],
            active_memory.id,
        )

    def test_build_person_context_rejects_person_from_another_user(self):
        other_user = get_user_model().objects.create_user(
            username="othercontextuser",
            email="othercontextuser@example.com",
            password="testpass123",
        )

        person = Person.objects.create(
            user=other_user,
            name="Rahul Sharma",
        )

        with self.assertRaises(ValueError):
            PersonContextService.build(
                user=self.user,
                person=person,
            ) 

    def test_build_person_context_rejects_cross_user_person_access(self):
        other_user = get_user_model().objects.create_user(
            username="crossuserperson",
            email="crossuserperson@example.com",
            password="testpass123",
        )

        person = Person.objects.create(
            user=other_user,
            name="Other User Person",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Person must belong to the same user as the context owner.",
        ):
            PersonContextService.build(
                user=self.user,
                person=person,
            )


    def test_build_person_context_does_not_expose_cross_user_person_data(self):
        other_user = get_user_model().objects.create_user(
            username="crossuserdata",
            email="crossuserdata@example.com",
            password="testpass123",
        )

        person = Person.objects.create(
            user=other_user,
            name="Private Person",
            phone_number="+919999999999",
            email="private@example.com",
            notes="Private cross-user information",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Person must belong to the same user as the context owner.",
        ):
            PersonContextService.build(
                user=self.user,
                person=person,
            )        

    def test_build_person_context_excludes_memory_owned_by_another_user(self):
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Owned Person",
        )

        other_user = get_user_model().objects.create_user(
            username="memoryotheruser",
            email="memoryotheruser@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=other_user,
            person=person,
            content="Private memory from another user",
            memory_type="fact",
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(context["memories"], [])


    def test_build_person_context_returns_only_memories_for_requested_person(self):
        from memory.models import Memory

        person = Person.objects.create(
            user=self.user,
            name="Requested Person",
        )

        other_person = Person.objects.create(
            user=self.user,
            name="Other Person",
        )

        Memory.objects.create(
            user=self.user,
            person=person,
            content="Memory for requested person",
            memory_type="fact",
        )

        Memory.objects.create(
            user=self.user,
            person=other_person,
            content="Memory for another person",
            memory_type="fact",
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertEqual(len(context["memories"]), 1)
        self.assertEqual(
            context["memories"][0]["content"],
            "Memory for requested person",
        )        

    def test_build_person_context_returns_none_for_inactive_person(self):
        person = Person.objects.create(
            user=self.user,
            name="Inactive Person",
            is_active=False,
        )

        context = PersonContextService.build(
            user=self.user,
            person=person,
        )

        self.assertIsNone(context)                           