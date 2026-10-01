from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    Language,
)
from unittest.mock import patch
from django.test import TestCase
from .services import (
    send_email_verification_email,
    send_password_reset_email,
)

from .serializers import (
    UserRegistrationSerializer,
    EmailVerificationTokenSerializer,
    PasswordResetTokenSerializer,
    NIRAPersonalProfileSerializer,    
)

from django.core.exceptions import (
    ValidationError,
)

from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    Language,
    NIRAPersonalProfile,
)

from .services import (
    send_email_verification_email,
    send_password_reset_email,
)
from .profile_services import (
    get_nira_personal_profile,
    create_nira_personal_profile,
    update_nira_personal_profile,
    validate_nira_personal_profile,
    get_or_create_nira_personal_profile,
    ensure_nira_profile_owner,
)

User = get_user_model()

class NIRAPersonalProfileArchitectureTestCase(APITestCase):
    def _create_test_user(self):
        self.user = User.objects.create_user(
            username="nira_profile_test_user",
            email="nira_profile_test@example.com",
            password="StrongPass123",
        )
        return self.user

    def _create_test_profile(self):
        if not hasattr(self, "user"):
            self._create_test_user()
        return NIRAPersonalProfile.objects.create(
            user=self.user,
        )
    
    def test_user_keeps_account_identity_fields(self):
        user_fields = {
            field.name
            for field in User._meta.get_fields()
        }

        expected_fields = {
            "username",
            "email",
            "first_name",
            "last_name",
            "email_verified",
            "email_verified_at",
            "whatsapp_phone_number",
            "preferred_language_ref",
            "voice_language_ref",
            "timezone",
        }

        self.assertTrue(
            expected_fields.issubset(user_fields)
        )

    def test_user_does_not_contain_nira_personalization_fields(self):
        user_fields = {
            field.name
            for field in User._meta.get_fields()
        }

        nira_personalization_fields = {
            "communication_style",
            "work_info",
            "skills",
            "interests",
            "custom_instructions",
            "privacy_settings",
            "memory_settings",
        }

        self.assertTrue(
            user_fields.isdisjoint(
                nira_personalization_fields
            )
        )

    def test_nira_personal_profile_has_expected_fields(self):
        from .models import NIRAPersonalProfile

        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        expected_fields = {
            "user",
            "languages",
            "communication_style",
            "work_info",
            "skills",
            "interests",
            "important_people",
            "custom_instructions",
            "privacy_settings",
            "memory_settings",
            "created_at",
            "updated_at",
        }

        self.assertTrue(
            expected_fields.issubset(profile_fields)
        )

    def test_nira_personal_profile_has_one_to_one_user_relationship(self):
        from .models import NIRAPersonalProfile

        user_field = NIRAPersonalProfile._meta.get_field("user")

        self.assertTrue(user_field.one_to_one)

    def test_nira_personal_profile_accepts_valid_data(self):
        from .models import NIRAPersonalProfile

        profile = NIRAPersonalProfile(
            user=self._create_test_user(),
            languages=["English", "Hindi"],
            communication_style={"tone": "friendly"},
            work_info={"role": "Developer"},
            skills=["Python"],
            interests=["AI"],
            important_people=[],
            custom_instructions="Be concise.",
            privacy_settings={"profile_visibility": "private"},
            memory_settings={"enabled": True},
        )

        profile.full_clean()

    def test_nira_personal_profile_rejects_non_list_collection_fields(self):
        from django.core.exceptions import ValidationError
        from .models import NIRAPersonalProfile

        profile = NIRAPersonalProfile(
            user=self._create_test_user(),
            languages="English",
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_nira_personal_profile_rejects_non_dict_settings_fields(self):
        from django.core.exceptions import ValidationError
        from .models import NIRAPersonalProfile

        profile = NIRAPersonalProfile(
            user=self._create_test_user(),
            communication_style="friendly",
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_nira_personal_profile_serializer_contains_expected_fields(self):
        serializer = NIRAPersonalProfileSerializer()

        expected_fields = {
            "id",
            "user",
            "languages",
            "communication_style",
            "work_info",
            "skills",
            "interests",
            "important_people",
            "custom_instructions",
            "privacy_settings",
            "memory_settings",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(serializer.fields.keys()),
            expected_fields,
        )

    def test_nira_personal_profile_serializer_has_read_only_fields(self):
        serializer = NIRAPersonalProfileSerializer()

        read_only_fields = {
            field_name
            for field_name, field in serializer.fields.items()
            if field.read_only
        }

        expected_read_only_fields = {
            "id",
            "user",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            read_only_fields,
            expected_read_only_fields,
        )

    def test_nira_personal_profile_serializer_serializes_profile(self):
        profile = self._create_test_profile()

        serializer = NIRAPersonalProfileSerializer(profile)

        self.assertEqual(
            serializer.data["user"],
            self.user.id,
        )
        self.assertEqual(
            serializer.data["languages"],
            [],
        )
        self.assertEqual(
            serializer.data["skills"],
            [],
        )
        self.assertEqual(
            serializer.data["interests"],
            [],
        )
        self.assertEqual(
            serializer.data["important_people"],
            [],
        )

    def test_nira_personal_profile_serializer_validates_profile_data(self):
        self._create_test_user()

        serializer = NIRAPersonalProfileSerializer(
            data={
                "languages": ["English"],
                "communication_style": {
                    "tone": "professional",
                },
                "work_info": {
                    "role": "Backend Developer",
                },
                "skills": ["Python", "Django"],
                "interests": ["AI"],
                "important_people": [],
                "custom_instructions": "Keep responses concise.",
                "privacy_settings": {
                    "profile_visibility": "private",
                },
                "memory_settings": {
                    "enabled": True,
                },
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_nira_personal_profile_serializer_rejects_invalid_collection_data(self):
        self._create_test_user()

        serializer = NIRAPersonalProfileSerializer(
            data={
                "languages": "English",
                "skills": "Python",
                "interests": "AI",
                "important_people": {},
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        profile = NIRAPersonalProfile(
            user=self.user,
            languages="English",
            skills="Python",
            interests="AI",
            important_people={},
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()         

    def test_get_nira_personal_profile_returns_user_profile(self):
        profile = self._create_test_profile()

        result = get_nira_personal_profile(self.user)

        self.assertEqual(result, profile)

    def test_create_nira_personal_profile_creates_profile(self):
        self._create_test_user()

        profile = create_nira_personal_profile(
            self.user,
            languages=["English"],
            skills=["Python"],
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.languages, ["English"])
        self.assertEqual(profile.skills, ["Python"])

    def test_update_nira_personal_profile_updates_profile(self):
        profile = self._create_test_profile()

        result = update_nira_personal_profile(
            profile,
            skills=["Python", "Django"],
        )

        self.assertEqual(result.skills, ["Python", "Django"])

    def test_validate_nira_personal_profile_returns_valid_profile(self):
        profile = self._create_test_profile()

        result = validate_nira_personal_profile(profile)

        self.assertEqual(result, profile)

    def test_get_or_create_nira_personal_profile_creates_default_profile(self):
        self._create_test_user()

        profile, created = get_or_create_nira_personal_profile(
            self.user
        )

        self.assertTrue(created)
        self.assertEqual(profile.user, self.user)

    def test_get_or_create_nira_personal_profile_returns_existing_profile(self):
        profile = self._create_test_profile()

        result, created = get_or_create_nira_personal_profile(
            self.user
        )

        self.assertFalse(created)
        self.assertEqual(result, profile)

    def test_ensure_nira_profile_owner_accepts_owner(self):
        profile = self._create_test_profile()

        result = ensure_nira_profile_owner(
            profile,
            self.user,
        )

        self.assertEqual(result, profile)

    def test_ensure_nira_profile_owner_rejects_different_user(self):
        profile = self._create_test_profile()

        another_user = User.objects.create_user(
            username="another_nira_user",
            email="another_nira_user@example.com",
            password="StrongPass123",
        )

        with self.assertRaises(PermissionError):
            ensure_nira_profile_owner(
                profile,
                another_user,
            )        

    def test_get_nira_personal_profile_returns_user_profile(self):
        profile = self._create_test_profile()

        result = get_nira_personal_profile(self.user)

        self.assertEqual(result, profile)

    def test_create_nira_personal_profile_creates_profile(self):
        self._create_test_user()

        profile = create_nira_personal_profile(
            self.user,
            languages=["English"],
            skills=["Python"],
        )

        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.languages, ["English"])
        self.assertEqual(profile.skills, ["Python"])

    def test_update_nira_personal_profile_updates_profile(self):
        profile = self._create_test_profile()

        result = update_nira_personal_profile(
            profile,
            skills=["Python", "Django"],
        )

        self.assertEqual(result.skills, ["Python", "Django"])

    def test_validate_nira_personal_profile_returns_valid_profile(self):
        profile = self._create_test_profile()

        result = validate_nira_personal_profile(profile)

        self.assertEqual(result, profile)

    def test_get_or_create_nira_personal_profile_creates_default_profile(self):
        self._create_test_user()

        profile, created = get_or_create_nira_personal_profile(
            self.user
        )

        self.assertTrue(created)
        self.assertEqual(profile.user, self.user)

    def test_get_or_create_nira_personal_profile_returns_existing_profile(self):
        profile = self._create_test_profile()

        result, created = get_or_create_nira_personal_profile(
            self.user
        )

        self.assertFalse(created)
        self.assertEqual(result, profile)

    def test_ensure_nira_profile_owner_accepts_owner(self):
        profile = self._create_test_profile()

        result = ensure_nira_profile_owner(
            profile,
            self.user,
        )

        self.assertEqual(result, profile)

    def test_ensure_nira_profile_owner_rejects_different_user(self):
        profile = self._create_test_profile()

        another_user = User.objects.create_user(
            username="another_nira_user",
            email="another_nira_user@example.com",
            password="StrongPass123",
        )

        with self.assertRaises(PermissionError):
            ensure_nira_profile_owner(
                profile,
                another_user,
            )   

    def test_nira_personal_profile_serializer_contains_expected_fields(self):
        serializer = NIRAPersonalProfileSerializer()

        expected_fields = {
            "id",
            "user",
            "languages",
            "communication_style",
            "work_info",
            "skills",
            "interests",
            "important_people",
            "custom_instructions",
            "privacy_settings",
            "memory_settings",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(serializer.fields.keys()),
            expected_fields,
        )


    def test_nira_personal_profile_serializer_has_read_only_fields(self):
        serializer = NIRAPersonalProfileSerializer()

        read_only_fields = {
            field_name
            for field_name, field in serializer.fields.items()
            if field.read_only
        }

        expected_read_only_fields = {
            "id",
            "user",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            read_only_fields,
            expected_read_only_fields,
        )


    def test_nira_personal_profile_serializer_serializes_profile(self):
        profile = self._create_test_profile()

        serializer = NIRAPersonalProfileSerializer(profile)

        self.assertEqual(
            serializer.data["user"],
            self.user.id,
        )
        self.assertEqual(
            serializer.data["languages"],
            [],
        )
        self.assertEqual(
            serializer.data["skills"],
            [],
        )
        self.assertEqual(
            serializer.data["interests"],
            [],
        )
        self.assertEqual(
            serializer.data["important_people"],
            [],
        )


    def test_nira_personal_profile_serializer_validates_profile_data(self):
        self._create_test_user()

        serializer = NIRAPersonalProfileSerializer(
            data={
                "languages": ["English"],
                "communication_style": {
                    "tone": "professional",
                },
                "work_info": {
                    "role": "Backend Developer",
                },
                "skills": ["Python", "Django"],
                "interests": ["AI"],
                "important_people": [],
                "custom_instructions": "Keep responses concise.",
                "privacy_settings": {
                    "profile_visibility": "private",
                },
                "memory_settings": {
                    "enabled": True,
                },
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )


    def test_nira_personal_profile_serializer_rejects_invalid_collection_data(self):
        self._create_test_user()

        serializer = NIRAPersonalProfileSerializer(
            data={
                "languages": "English",
                "skills": "Python",
                "interests": "AI",
                "important_people": {},
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        profile = NIRAPersonalProfile(
            user=self.user,
            languages="English",
            skills="Python",
            interests="AI",
            important_people={},
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()   

    def test_nira_personal_profile_api_requires_authentication(self):
        response = self.client.get(
            "/api/auth/nira-profile/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_nira_personal_profile_api_returns_profile(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/auth/nira-profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["user"],
            self.user.id,
        )

    def test_nira_personal_profile_api_returns_expected_profile_fields(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            "/api/auth/nira-profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        expected_fields = {
            "id",
            "user",
            "languages",
            "communication_style",
            "work_info",
            "skills",
            "interests",
            "important_people",
            "custom_instructions",
            "privacy_settings",
            "memory_settings",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(response.data.keys()),
            expected_fields,
        )    

    def test_nira_personal_profile_api_creates_missing_profile(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        self.assertFalse(
            NIRAPersonalProfile.objects.filter(
                user=self.user,
            ).exists()
        )

        response = self.client.get(
            "/api/auth/nira-profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTrue(
            NIRAPersonalProfile.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_nira_personal_profile_api_does_not_return_another_users_profile(self):
        self._create_test_user()

        profile = self._create_test_profile()

        another_user = User.objects.create_user(
            username="nira_api_other_user",
            email="nira_api_other@example.com",
            password="StrongPass123",
        )

        self.client.force_authenticate(
            user=another_user,
        )

        response = self.client.get(
            "/api/auth/nira-profile/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertNotEqual(
            response.data["user"],
            profile.user_id,
        )
        self.assertEqual(
            response.data["user"],
            another_user.id,
        ) 

    def test_nira_personal_profile_api_patch_does_not_modify_another_users_profile(self):
        self._create_test_user()

        other_user = User.objects.create_user(
            username="nira_other_user",
            email="nira_other_user@example.com",
            password="StrongPass123",
        )

        other_profile = NIRAPersonalProfile.objects.create(
            user=other_user,
            skills=["Original Skill"],
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            "/api/auth/nira-profile/",
            {
                "skills": ["Modified Skill"],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        other_profile.refresh_from_db()

        self.assertEqual(
            other_profile.skills,
            ["Original Skill"],
        )         

    def test_nira_personal_profile_api_updates_profile(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            "/api/auth/nira-profile/",
            {
                "skills": ["Python", "Django"],
                "interests": ["AI", "Machine Learning"],
                "custom_instructions": "Keep responses concise.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["skills"],
            ["Python", "Django"],
        )
        self.assertEqual(
            response.data["interests"],
            ["AI", "Machine Learning"],
        )
        self.assertEqual(
            response.data["custom_instructions"],
            "Keep responses concise.",
        )

    def test_nira_personal_profile_api_requires_authentication_for_patch(self):
        response = self.client.patch(
            "/api/auth/nira-profile/",
            {
                "skills": ["Python"],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_nira_personal_profile_api_patch_preserves_existing_fields(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        profile = self._create_test_profile()
        profile.skills = ["Python"]
        profile.interests = ["AI"]
        profile.custom_instructions = "Be concise."
        profile.save()

        response = self.client.patch(
            "/api/auth/nira-profile/",
            {
                "skills": ["Python", "Django"],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["skills"],
            ["Python", "Django"],
        )
        self.assertEqual(
            response.data["interests"],
            ["AI"],
        )
        self.assertEqual(
            response.data["custom_instructions"],
            "Be concise.",
        )  

    def test_nira_personal_profile_api_patch_returns_validation_error(self):
        self._create_test_user()

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.patch(
            "/api/auth/nira-profile/",
            {
                "skills": {
                    "invalid": "collection",
                },
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "skills",
            response.data,
        )  

    def test_preferred_language_is_reused_from_user_account(self):
        self.assertTrue(
            hasattr(User, "preferred_language_ref"),
        )

        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertNotIn(
            "preferred_language",
            profile_fields,
        )                  

    def test_voice_language_is_reused_from_user_account(self):
        self.assertTrue(
            hasattr(User, "voice_language_ref"),
        )

        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertNotIn(
            "voice_language",
            profile_fields,
        )         

    def test_response_style_is_stored_in_communication_style(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "communication_style",
            profile_fields,
        )

        self.assertNotIn(
            "response_style",
            profile_fields,
        )    

    def test_formality_preference_is_stored_in_communication_style(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "communication_style",
            profile_fields,
        )

        self.assertNotIn(
            "formality",
            profile_fields,
        )

        self.assertNotIn(
            "formal_casual",
            profile_fields,
        )    

    def test_response_length_is_stored_in_communication_style(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "communication_style",
            profile_fields,
        )

        self.assertNotIn(
            "response_length",
            profile_fields,
        )    

    def test_channel_preferences_are_stored_in_communication_style(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "communication_style",
            profile_fields,
        )

        self.assertNotIn(
            "channel_preferences",
            profile_fields,
        )    

    def test_communication_style_supports_channel_specific_preferences(self):
        profile = self._create_test_profile()

        profile.communication_style = {
            "response_style": "concise",
            "formality": "professional",
            "response_length": "short",
            "channels": {
                "whatsapp": {
                    "response_length": "short",
                },
                "sms": {
                    "response_length": "very_short",
                },
                "call": {
                    "response_style": "conversational",
                },
            },
        }

        profile.full_clean()

        self.assertEqual(
            profile.communication_style["channels"]["whatsapp"][
                "response_length"
            ],
            "short",
        )

        self.assertEqual(
            profile.communication_style["channels"]["sms"][
                "response_length"
            ],
            "very_short",
        )

        self.assertEqual(
            profile.communication_style["channels"]["call"][
                "response_style"
            ],
            "conversational",
        )    

    def test_communication_style_supports_all_phase_2_preferences(self):
        profile = self._create_test_profile()

        profile.communication_style = {
            "response_style": "clear",
            "formality": "professional",
            "response_length": "concise",
            "channels": {
                "whatsapp": {
                    "response_length": "short",
                },
                "sms": {
                    "response_length": "very_short",
                },
                "call": {
                    "response_style": "conversational",
                },
            },
        }

        profile.full_clean()

        communication_style = profile.communication_style

        self.assertEqual(
            communication_style["response_style"],
            "clear",
        )

        self.assertEqual(
            communication_style["formality"],
            "professional",
        )

        self.assertEqual(
            communication_style["response_length"],
            "concise",
        )

        self.assertIn(
            "channels",
            communication_style,
        )

        self.assertIn(
            "whatsapp",
            communication_style["channels"],
        )

        self.assertIn(
            "sms",
            communication_style["channels"],
        )

        self.assertIn(
            "call",
            communication_style["channels"],
        )    

    def test_professional_communication_uses_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "professional_communication",
            profile_fields,
        )    

    def test_preferred_response_behavior_uses_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "preferred_response_behavior",
            profile_fields,
        )    

    def test_always_ask_before_sending_uses_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "always_ask_before_sending",
            profile_fields,
        )    

    def test_unknown_contact_rule_uses_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "unknown_contact_rule",
            profile_fields,
        )    

    def test_language_preferences_rule_uses_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "language_preferences_rule",
            profile_fields,
        )    

    def test_personal_rules_use_custom_instructions(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "custom_instructions",
            profile_fields,
        )

        self.assertNotIn(
            "personal_rules",
            profile_fields,
        )    

    def test_custom_instructions_store_user_defined_rules(self):
        profile = self._create_test_profile()

        profile.custom_instructions = (
            "Use professional communication. "
            "Keep responses concise. "
            "Always ask before sending messages. "
            "Do not reply to unknown contacts. "
            "Reply in Hindi unless I request another language. "
            "Ask when my request is ambiguous."
        )

        profile.full_clean()
        profile.save()

        profile.refresh_from_db()

        self.assertIn(
            "Use professional communication.",
            profile.custom_instructions,
        )

        self.assertIn(
            "Always ask before sending messages.",
            profile.custom_instructions,
        )

        self.assertIn(
            "Do not reply to unknown contacts.",
            profile.custom_instructions,
        )

        self.assertIn(
            "Reply in Hindi unless I request another language.",
            profile.custom_instructions,
        )

        self.assertIn(
            "Ask when my request is ambiguous.",
            profile.custom_instructions,
        )    

    def test_custom_instructions_are_preserved_during_profile_update(self):
        profile = self._create_test_profile()

        profile.custom_instructions = (
            "Always ask before sending messages."
        )
        profile.save()

        from users.profile_services import (
            update_nira_personal_profile,
        )

        update_nira_personal_profile(
            profile,
            interests=["AI", "Python"],
        )

        profile.refresh_from_db()

        self.assertEqual(
            profile.custom_instructions,
            "Always ask before sending messages.",
        )

        self.assertEqual(
            profile.interests,
            ["AI", "Python"],
        )    

    def test_empty_custom_instructions_are_valid(self):
        profile = self._create_test_profile()

        profile.custom_instructions = ""

        profile.full_clean()
        profile.save()

        profile.refresh_from_db()

        self.assertEqual(
            profile.custom_instructions,
            "",
        )    

    def test_profile_privacy_uses_privacy_settings(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "privacy_settings",
            profile_fields,
        )

        self.assertNotIn(
            "profile_privacy",
            profile_fields,
        )    

    def test_ai_usage_control_uses_privacy_settings(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "privacy_settings",
            profile_fields,
        )

        self.assertNotIn(
            "ai_usage_enabled",
            profile_fields,
        )    

    def test_memory_permission_uses_memory_settings(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "memory_settings",
            profile_fields,
        )

        self.assertNotIn(
            "memory_permission",
            profile_fields,
        )    

    def test_cloud_ai_preference_uses_privacy_settings(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "privacy_settings",
            profile_fields,
        )

        self.assertNotIn(
            "cloud_ai_preference",
            profile_fields,
        )    

    def test_sensitive_information_controls_use_privacy_settings(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "privacy_settings",
            profile_fields,
        )

        self.assertNotIn(
            "sensitive_information_controls",
            profile_fields,
        )    

    def test_profile_deletion_is_supported_by_user_ownership(self):
        profile_fields = {
            field.name
            for field in NIRAPersonalProfile._meta.get_fields()
        }

        self.assertIn(
            "user",
            profile_fields,
        )

        self.assertEqual(
            NIRAPersonalProfile._meta.get_field("user").one_to_one,
            True,
        )    

    def test_privacy_and_ai_controls_store_expected_settings(self):
        profile = self._create_test_profile()

        profile.privacy_settings = {
            "profile_visible_to_ai": True,
            "ai_usage_enabled": True,
            "cloud_ai_enabled": False,
            "sensitive_information": {
                "allow_processing": False,
            },
        }

        profile.memory_settings = {
            "enabled": True,
        }

        profile.full_clean()
        profile.save()

        profile.refresh_from_db()

        self.assertTrue(
            profile.privacy_settings["profile_visible_to_ai"],
        )

        self.assertTrue(
            profile.privacy_settings["ai_usage_enabled"],
        )

        self.assertFalse(
            profile.privacy_settings["cloud_ai_enabled"],
        )

        self.assertFalse(
            profile.privacy_settings["sensitive_information"][
                "allow_processing"
            ],
        )

        self.assertTrue(
            profile.memory_settings["enabled"],
        )    

    def test_privacy_and_ai_controls_can_be_disabled(self):
        profile = self._create_test_profile()

        profile.privacy_settings = {
            "profile_visible_to_ai": False,
            "ai_usage_enabled": False,
            "cloud_ai_enabled": False,
            "sensitive_information": {
                "allow_processing": False,
            },
        }

        profile.memory_settings = {
            "enabled": False,
        }

        profile.full_clean()
        profile.save()

        profile.refresh_from_db()

        self.assertFalse(
            profile.privacy_settings["profile_visible_to_ai"],
        )

        self.assertFalse(
            profile.privacy_settings["ai_usage_enabled"],
        )

        self.assertFalse(
            profile.privacy_settings["cloud_ai_enabled"],
        )

        self.assertFalse(
            profile.privacy_settings["sensitive_information"][
                "allow_processing"
            ],
        )

        self.assertFalse(
            profile.memory_settings["enabled"],
        )    

class UserLoginAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123",
            email_verified=True,
        )

    def test_user_login_return_tokens(self):
        data = {
            "username": "loginuser",
            "password": "StrongPass123",
        }

        response = self.client.post(
            "/api/auth/login/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])

    def test_invallid_password_is_rejected(self):
        data = {
            "username": "loginuser",
            "password": "WrongPassword123",
        }

        response = self.client.post(
            "/api/auth/login/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_token_return_new_access_token(self):
        login_data = {
            "username": "loginuser",
            "password": "StrongPass123",
        }

        login_response = self.client.post(
            "/api/auth/login/",
            login_data, format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        refresh_token = login_response.data["refresh"]
        response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertTrue(response.data["access"])

    def test_current_user_requires_authentication(self):
        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_return_authenticated_user(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format='json',
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "loginuser",
        )

        self.assertEqual(
            response.data["email"],
            "login@example.com",
        )

    def test_logout_blacklist_refresh_token(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        logout_response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            logout_response.data["message"],
            "Successfully logged out.",
        )

        refresh_response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_requires_authentication(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": refresh_token,
            },
            format ="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            "/api/auth/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_profile_returns_authentication_user(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            fromat="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "loginuser",
        )

        self.assertEqual(
            response.data["email"],
            "login@example.com",
        )

    def test_update_profile(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.patch(
            "/api/auth/profile/",
            {
                "first_name": "Updated",
                "last_name": "User",
                "preferred_language": "en",
                "voice_language": "hi",
                "timezone": "Asia/Kolkata",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["first_name"],
            "Updated",
        )

        self.assertEqual(
            response.data["voice_language"],
            "hi",
        )

        self.assertEqual(
            response.data["timezone"],
            "Asia/Kolkata",
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertEqual(
            user.first_name,
            "Updated",
        )

        self.assertEqual(
            user.voice_language_ref.code,
            "hi",
        )

    def test_profile_cannot_update_username_or_email(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.patch(
            "/api/auth/profile/",
            {
                "username": "changed_username",
                "email": "changed@example.com",
                "first_name": "Protected",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertEqual(
            user.username,
            "loginuser",
        )

        self.assertEqual(
            user.email,
            "login@example.com",
        )

        self.assertEqual(
            user.first_name,
            "Protected",
        )

    def test_change_password_requires_authentication(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_change_password_success(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            "Password changed successfully.",
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertTrue(
            user.check_password("NewStrongPass456")
        )

        self.assertFalse(
            user.check_password("StrongPass123")
        )

    def test_change_password_rejects_wrong_old_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "WrongPassword123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "old_password", response.data,
        )

    def test_change_password_rejects_same_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password", response.data,
        )

    def test_change_password_rejects_short_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password", response.data,
        )

    def test_unverified_email_cannot_login(self):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )

        self.assertEqual(
            response.data["email"][0],
            "Please verify your email address before logging in.",
        )

        self.assertNotIn(
            "access",
            response.data,
        )

        self.assertNotIn(
            "refresh",
            response.data,
        )    


class UserRegistrationSerializerTestCase(APITestCase):
    def test_valid_user_registration(self):
        data = {
            "username": "sahil",
            "email": "sahil@786.com",
            "password": "StrongPass123",
            "first_name": "Sahil",
            "last_name": "Siddiquie",
            "preferred_language": "en",
            "voice_language": "hi",
            "timezone": "Asia/KolKata",
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "sahil@786.com")
        self.assertEqual(user.first_name, "Sahil")
        self.assertEqual(user.preferred_language_ref.code, "en")

        # Password must be stored as plain text.
        self.assertNotEqual(user.password, "StrongPass123")

        # Django should be able to verify the password.
        self.assertTrue(user.check_password("StrongPass123"))

    def test_short_password_is_rejected(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

class UserRegistrationAPITestCase(APITestCase):

    def test_user_registration_api(self):

        data = {
            "username": "apiuser",
            "email": "apiuser@example.com",
            "password": "StrongPass123",
            "first_name": "API",
            "last_name": "User",
            "preferred_language": "en",
            "voice_language": "hi",
            "timezone": "Asia/Kolkata",
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["message"],
            "User registered successfully.",
        )

        self.assertEqual(
            response.data["user"]["email"],
            "apiuser@example.com",
        )

        self.assertTrue(
            User.objects.filter(
                email="apiuser@example.com"
            ).exists()
        )

    @patch("users.views.send_email_verification_email")
    def test_registration_sends_verification_email(self, mock_send_email):
        data = {
            "username": "emailtestuser",
            "email": "emailtest@example.com",
            "password": "StrongPass123",
            "first_name": "Email",
            "last_name": "Test",
            "preferred_language": "en",
            "voice_language": "hi",
            "timezone": "Asia/Kolkata",
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user.email,
            "emailtest@example.com",
        )

        self.assertEqual(
            called_token.user,
            called_user,
        )

        self.assertFalse(
            called_token.used,
        )    

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123",
        )

        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "StrongPass123",
        } 

        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("email", response.data)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123",
        )

        data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "StrongPass123",
        }

        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("username", response.data)

    def test_missing_email_is_rejected(self):
        data = {
            "username": "missingemail",
            "password": "StrongPass123",
        } 
        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("email", response.data) 

class EmailVerificationTokenTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="verificationuser",
            email="verification@example.com",
            password="StrongPass123",
        )

    def test_verification_token_is_created(self):
        serializer = EmailVerificationTokenSerializer()

        token = serializer.create_token(self.user)

        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        self.assertFalse(token.is_expired())

    def test_old_unused_tokens_are_invalidated(self):
        serializer = EmailVerificationTokenSerializer()

        first_token = serializer.create_token(self.user)
        second_token = serializer.create_token(self.user)

        first_token.refresh_from_db()

        self.assertTrue(first_token.used)
        self.assertFalse(second_token.used)

    def test_token_expires_after_expiration_time(self):
        serializer = EmailVerificationTokenSerializer()

        token = serializer.create_token(self.user)

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        self.assertTrue(token.is_expired())    

class EmailVerificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="verifyuser",
            email="verify@example.com",
            password="StrongPass123",
        )

    def create_token(self):
        serializer = EmailVerificationTokenSerializer()
        return serializer.create_token(self.user)

    def test_valid_token_verifies_email(self):
        token = self.create_token()

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()
        token.refresh_from_db()

        self.assertTrue(self.user.email_verified)
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertTrue(token.used)

        self.assertEqual(
            response.data["message"],
            "Email verified successfully.",
        )

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": "550e8400-e29b-41d4-a716-446655440000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_expired_token_is_rejected(self):
        token = self.create_token()

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()
        token.refresh_from_db()

        self.assertFalse(self.user.email_verified)
        self.assertFalse(token.used)

    def test_used_token_is_rejected(self):
        token = self.create_token()

        token.used= True
        token.save(update_fields=["used"])

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            fromat="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

class ResendVerificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resenduser",
            email="resend@example.com",
            password="StrongPass123",
            email_verified=False,
        )

    @patch("users.views.send_email_verification_email")
    def test_resend_verification_sends_email(
        self,
        mock_send_email,
    ):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a verification email has been sent."
            ),
        )

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user,
            self.user,
        )

        self.assertEqual(
            called_token.user,
            self.user,
        )

        self.assertFalse(
            called_token.used,
        ) 

    def test_resend_verification_invalidates_old_token(self):
        token_serializer = EmailVerificationTokenSerializer()

        old_token = token_serializer.create_token(self.user)

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        old_token.refresh_from_db()

        self.assertTrue(
            old_token.used,
        )

        self.assertEqual(
            PasswordResetToken.objects.filter(
                user=self.user,
            ).count(),
            0,
        )

        self.assertEqual(
            EmailVerificationToken.objects.filter(
                user=self.user,
                used=False,
            ).count(),
            1,
        )

    def test_resend_verification_unknown_email(self):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "unknown@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a verification email has been sent."
            ),
        )

    def test_resend_verification_already_verified(self):
        self.user.email_verified = True
        self.user.save(
            update_fields=["email_verified"],
        )

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )

        self.assertEqual(
            response.data["email"][0],
            "Email address is already verified.",
        )

    def test_resend_verification_invalid_email(self):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )                   

class PasswordResetTokenTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="StrongPass123",
        )

    def test_password_reset_token_is_created(self):
        serializer = PasswordResetTokenSerializer()

        token = serializer.create_token(self.user)

        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        self.assertFalse(token.is_expired())

    def test_old_reset_token_are_invalidated(self):
        serializer = PasswordResetTokenSerializer()

        first_token = serializer.create_token(self.user)
        second_token = serializer.create_token(self.user)

        first_token.refresh_from_db()

        self.assertTrue(first_token.used)
        self.assertFalse(second_token.used)

    def test_reset_token_expires(self):
        serializer =PasswordResetTokenSerializer()

        token = serializer.create_token(self.user)

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        self.assertTrue(token.is_expired())

class ForgotPasswordAPItestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="forgotuser",
            email="forgot@example.com",
            password="StrongPass123",
        )

    def test_forgot_password_existing_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "forgot@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a password reset link has been sent."
            ),
        )

        self.assertTrue(
            PasswordResetToken.objects.filter(
                user=self.user,
                used=False,
            ).exists()
        )
    @patch("users.views.send_password_reset_email")
    def test_forgot_password_sends_reset_email(self, mock_send_email):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "forgot@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user,
            self.user,
        )

        self.assertEqual(
            called_token.user,
            self.user,
        )

        self.assertFalse(
            called_token.used,
        ) 

       
    def test_forgot_password_unknow_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "unknow@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a password reset link has been sent."
            ),
        )

    def test_forgot_password_invalid_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )       

class ResetPasswordAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetapiuser",
            email="resetapi@example.com",
            password="OldPassword123",
        )

        serializer = PasswordResetTokenSerializer()
        self.token = serializer.create_token(self.user)

    def test_reset_password_success(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            "Password reset successfully.",
        )

        self.user.refresh_from_db()
        self.token.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword123")
        )

        self.assertTrue(self.token.used)

    def test_invalid_reset_token_is_rejected(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": "550e8400-e29b-41d4-a716-446655440000",
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_used_reset_token_is_rejected(self):
        self.token.used = True
        self.token.save(update_fields=["used"])

        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_expired_reset_token_is_rejected(self):
        self.token.expires_at = timezone.now() - timedelta(minutes=1)
        self.token.save(update_fields=["expires_at"])

        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_new_password_is_required(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

class EmailServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="emailserviceuser",
            email="emailservice@example.com",
            password="StrongPass123",
        )

    @patch("users.services.send_mail")
    def test_send_email_verification_email(self, mock_send_mail):
        serializer = EmailVerificationTokenSerializer()
        token = serializer.create_token(self.user)

        send_email_verification_email(
            self.user,
            token,
        )

        mock_send_mail.assert_called_once()

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertEqual(
            call_kwargs["subject"],
            "Verify your email",
        )

        self.assertEqual(
            call_kwargs["recipient_list"],
            ["emailservice@example.com"],
        )

        self.assertIn(
            str(token.token),
            call_kwargs["message"],
        )

    @patch("users.services.send_mail")
    def test_send_password_reset_email(self, mock_send_mail):
        serializer = PasswordResetTokenSerializer()
        token = serializer.create_token(self.user)

        send_password_reset_email(
            self.user,
            token,
        )

        mock_send_mail.assert_called_once()

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertEqual(
            call_kwargs["subject"],
            "Reset your password",
        )

        self.assertEqual(
            call_kwargs["recipient_list"],
            ["emailservice@example.com"],
        )

        self.assertIn(
            str(token.token),
            call_kwargs["message"],
        )

class LanguageListAPITestCase(APITestCase):
    def setUp(self):
        self.active_language = Language.objects.create(
            name="Test English",
            code="test-en",
            native_name="Test English",
            is_active=True,
        )

        self.second_active_language = Language.objects.create(
            name="Test Hindi",
            code='test-hi',
            native_name="परीक्षण हिन्दी",
            is_active=True,
        )

        self.inactive_language = Language.objects.create(
            name="Test French",
            code="test-fr",
            native_name="Test Francias",
            is_active=False,      
        )

    def test_language_list_returns_active_languages(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_codes = [
            language["code"]
            for language in response.data
        ]

        self.assertIn(
            "test-en",
            returned_codes,
        )

        self.assertIn(
            "test-hi",
            returned_codes,
        )

        self.assertNotIn(
            "test-fr",
            returned_codes,
        )

    def test_inactive_language_is_not_returned(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_codes = [
            language["code"]
            for language in response.data
        ]

        self.assertNotIn(
            "test-fr",
            returned_codes,
        )

    def test_language_list_is_ordered_by_name(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        names = [
            language["name"]
            for language in response.data
        ]

        self.assertEqual(
            names,
            sorted(names),
        )            