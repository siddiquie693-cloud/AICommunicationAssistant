
from django.test import SimpleTestCase

from ai.android.registry import ActionRegistry
from ai.android.registry_types import ActionDefinition
from ai.safety.types import SafetyLevel


class ActionRegistryTests(SimpleTestCase):

    def setUp(self):
        self.registry = ActionRegistry()

        self.registry.register(
            ActionDefinition(
                name="open_app",
                required_parameters=("app",),
                parameter_types={"app": str},
                risk_level=SafetyLevel.LOW,
            )
        )

    def test_register_and_get_action(self):
        definition = self.registry.get("open_app")

        self.assertIsNotNone(definition)
        self.assertEqual(definition.name, "open_app")

    def test_reject_duplicate_action(self):
        with self.assertRaises(ValueError):
            self.registry.register(
                ActionDefinition(name="open_app")
            )

    def test_reject_invalid_definition_type(self):
        with self.assertRaises(TypeError):
            self.registry.register("open_app")

    def test_validate_valid_action(self):
        result = self.registry.validate(
            "open_app",
            {"app": "calculator"},
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.risk_level, SafetyLevel.LOW)
        self.assertEqual(
            result.validated_parameters,
            {"app": "calculator"},
        )

    def test_reject_unregistered_action(self):
        result = self.registry.validate(
            "delete_files",
            {},
        )

        self.assertFalse(result.is_valid)
        self.assertIn(
            "Unregistered action: delete_files.",
            result.errors,
        )

    def test_reject_missing_required_parameter(self):
        result = self.registry.validate(
            "open_app",
            {},
        )

        self.assertFalse(result.is_valid)
        self.assertIn(
            "Missing required parameter: app.",
            result.errors,
        )

    def test_reject_invalid_parameter_type(self):
        result = self.registry.validate(
            "open_app",
            {"app": 123},
        )

        self.assertFalse(result.is_valid)

    def test_reject_unsupported_parameter(self):
        result = self.registry.validate(
            "open_app",
            {
                "app": "calculator",
                "admin": True,
            },
        )

        self.assertFalse(result.is_valid)
        self.assertIn(
            "Unsupported parameter: admin.",
            result.errors,
        )

    def test_reject_empty_required_string(self):
        result = self.registry.validate(
            "open_app",
            {"app": "   "},
        )

        self.assertFalse(result.is_valid)