from django.test import TestCase

class RAGContextBuilderTestCase(TestCase):
    def test_build_includes_profile_context(self):
        from .services.context import RAGContextBuilder

        builder = RAGContextBuilder()

        result = builder.build(
            [
                ("Python is a programming language.", 0.95),
            ],
            profile_context="User prefers concise responses.",
        )

        self.assertIn(
            "User prefers concise responses.",
            result,
        )
        self.assertIn(
            "Python is a programming language.",
            result,
        )

    def test_build_works_without_profile_context(self):
        from .services.context import RAGContextBuilder

        builder = RAGContextBuilder()

        result = builder.build(
            [
                ("Python is a programming language.", 0.95),
            ],
        )

        self.assertEqual(
            result,
            "Python is a programming language.",
        )

class NIRAPersonalProfileContextServiceTestCase(TestCase):
    def setUp(self):
        from users.models import User, NIRAPersonalProfile

        self.user = User.objects.create_user(
            username="profile_context_test_user",
            email="profile_context_test@example.com",
            password="StrongPass123",
        )

        self.profile = NIRAPersonalProfile.objects.create(
            user=self.user,
        )

    def test_build_returns_structured_profile_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.languages = ["English", "Hindi"]
        self.profile.communication_style = {
            "tone": "professional",
        }
        
        self.profile.interests = ["AI", "Technology"]
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="general",
        )

        self.assertIn("Personal Profile:", result)
        self.assertIn("Languages:", result)
        self.assertIn("English", result)
        self.assertIn("Communication Style:", result)
        self.assertIn("professional", result)
        self.assertIn("Interests:", result)
        self.assertIn("AI", result)

    def test_build_omits_empty_profile_fields(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.skills = ["Python"]
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="work",
        )

        self.assertIn("Personal Profile:", result)
        self.assertIn("Skills:", result)
        self.assertIn("Python", result)

        self.assertNotIn("Work Information:", result)
        self.assertNotIn("language:", result)
        self.assertNotIn("communication Style:", result)
        self.assertNotIn("Interests:", result)
        self.assertNotIn("Important People:", result)
        self.assertNotIn("Custom Instructions:", result)
        self.assertNotIn("Privacy Settings:", result)
        self.assertNotIn("Memory Settings:", result)

    def test_build_returns_empty_string_for_empty_profile(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        service = NIRAPersonalProfileContextService()

        result = service.build(self.profile)

        self.assertEqual(result, "")

    def test_build_does_not_include_account_identity_fields(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        service = NIRAPersonalProfileContextService()

        result = service.build(self.profile)

        self.assertNotIn(self.user.email, result)
        self.assertNotIn(self.user.username, result)
        self.assertNotIn("email:", result.lower())
        self.assertNotIn("username:", result.lower())

    def test_build_filters_profile_fields_for_work_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.languages = ["English"]
        self.profile.communication_style = {
            "tone": "professional",
        }
        self.profile.work_info = {
            "role": "Python Backend Developer",
        }
        self.profile.skills = ["Python", "Django"]
        self.profile.interests = ["AI"]
        self.profile.important_people = [
            {"name": "Test Person"},
        ]
        self.profile.custom_instructions = (
            "Keep responses concise."
        )
        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="work",
        )

        self.assertIn("Work Information:", result)
        self.assertIn("Python Backend Developer", result)
        self.assertIn("Skills:", result)
        self.assertIn("Django", result)

        self.assertNotIn("Languages:", result)
        self.assertNotIn("Communication Style:", result)
        self.assertNotIn("Interests:", result)
        self.assertNotIn("Important People:", result)
        self.assertNotIn("Custom Instructions:", result)
        self.assertNotIn("Privacy Settings:", result)
        self.assertNotIn("Memory Settings:", result)

    def test_build_filters_profile_fields_for_communication_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.languages = ["English", "Hindi"]
        self.profile.communication_style = {
            "tone": "casual",
        }
        self.profile.work_info = {
            "role": "Developer",
        }
        self.profile.skills = ["Python"]
        self.profile.interests = ["AI"]
        self.profile.important_people = [
            {"name": "Test Person"},
        ]
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="communication",
        )

        self.assertIn("Languages:", result)
        self.assertIn("English", result)
        self.assertIn("Communication Style:", result)
        self.assertIn("casual", result)
        self.assertIn("Important People:", result)
        self.assertIn("Test Person", result)

        self.assertNotIn("Work Information:", result)
        self.assertNotIn("Skills:", result)
        self.assertNotIn("Interests:", result)
        self.assertNotIn("Custom Instructions:", result)
        self.assertNotIn("Privacy Settings:", result)
        self.assertNotIn("Memory Settings:", result)

    def test_build_filters_profile_fields_for_instructions_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.custom_instructions = (
            "Always ask before sending messages."
        )
        self.profile.work_info = {
            "role": "Developer",
        }
        self.profile.skills = ["Python"]
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="instructions",
        )

        self.assertIn("Custom Instructions:", result)
        self.assertIn(
            "Always ask before sending messages.",
            result,
        )

        self.assertNotIn("Work Information:", result)
        self.assertNotIn("Skills:", result)

    def test_build_rejects_unsupported_context_purpose(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        service = NIRAPersonalProfileContextService()

        with self.assertRaises(ValueError):
            service.build(
                self.profile,
                context_purpose="unsupported",
            )    

    def test_build_does_not_expose_protected_fields_in_general_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.languages = ["English"]
        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="general",
        )

        self.assertIn("Languages:", result)
        self.assertNotIn("Privacy Settings:", result)
        self.assertNotIn("Memory Settings:", result)

    def test_build_does_not_expose_protected_fields_in_work_context(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.work_info = {
            "role": "Developer",
        }
        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        result = service.build(
            self.profile,
            context_purpose="work",
        )

        self.assertIn("Work Information:", result)
        self.assertNotIn("Privacy Settings:", result)
        self.assertNotIn("Memory Settings:", result)

    def test_build_allows_protected_fields_only_in_explicit_contexts(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        service = NIRAPersonalProfileContextService()

        privacy_result = service.build(
            self.profile,
            context_purpose="privacy",
        )
        memory_result = service.build(
            self.profile,
            context_purpose="memory",
        )

        self.assertIn("Privacy Settings:", privacy_result)
        self.assertNotIn("Memory Settings:", privacy_result)

        self.assertIn("Memory Settings:", memory_result)
        self.assertNotIn("Privacy Settings:", memory_result)   

    def test_build_rejects_unapproved_profile_field_exposure(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        service = NIRAPersonalProfileContextService()

        original_fields = set(
            service.CONTEXT_FIELD_GROUPS["general"]
        )

        service.CONTEXT_FIELD_GROUPS["general"] = {
            *original_fields,
            "unapproved_field",
        }
        try:

            with self.assertRaises(ValueError):
                service.build(
                    self.profile,
                    context_purpose="general",
                )   
        finally:
            service.CONTEXT_FIELD_GROUPS["general"] = (
                original_fields
            )        

    def test_build_allows_only_registered_profile_fields(self):
        from .services.profile_context import (
            NIRAPersonalProfileContextService,
        )

        service = NIRAPersonalProfileContextService()

        supported_fields = {
            field_name
            for field_name, _label in service.PROFILE_FIELDS
        }

        for context_purpose, allowed_fields in (
            service.CONTEXT_FIELD_GROUPS.items()
        ):
            with self.subTest(
                context_purpose=context_purpose,
            ):
                self.assertTrue(
                    allowed_fields <= supported_fields
                )              
