
from django.test import SimpleTestCase

from ai.planner.types import ActionPlan, PlannedAction
from ai.planner.validator import ActionPlanValidator


class ActionPlanValidatorTests(SimpleTestCase):

    def setUp(self):
        self.validator = ActionPlanValidator()

    def test_valid_action_dependencies(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="resolve_contact",
                    action_id="action_1",
                ),
                PlannedAction(
                    name="send_message",
                    action_id="action_2",
                    depends_on=("action_1",),
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, ())

    def test_duplicate_action_ids_are_rejected(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(name="open_app", action_id="action_1"),
                PlannedAction(name="send_message", action_id="action_1"),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Duplicate action ID" in error for error in result.errors)
        )

    def test_unknown_dependency_is_rejected(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="send_message",
                    action_id="action_2",
                    depends_on=("missing_action",),
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("Unknown dependency ID" in error for error in result.errors)
        )

    def test_self_dependency_is_rejected(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="send_message",
                    action_id="action_1",
                    depends_on=("action_1",),
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("cannot depend on itself" in error for error in result.errors)
        )

    def test_dependency_must_appear_before_dependent_action(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="send_message",
                    action_id="action_2",
                    depends_on=("action_1",),
                ),
                PlannedAction(
                    name="resolve_contact",
                    action_id="action_1",
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("must appear before" in error for error in result.errors)
        )

    def test_dependencies_require_action_id(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="send_message",
                    depends_on=("action_1",),
                ),
                PlannedAction(
                    name="resolve_contact",
                    action_id="action_1",
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("requires an action ID" in error for error in result.errors)
        )

    def test_invalid_plan_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.validator.validate("not an action plan")

    def test_circular_dependencies_are_rejected(self):
        plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="action_a",
                    action_id="action_a",
                    depends_on=("action_b",),
                ),
                PlannedAction(
                    name="action_b",
                    action_id="action_b",
                    depends_on=("action_a",),
                ),
            ]
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)

    def test_plan_requiring_clarification_is_invalid(self):
        plan = ActionPlan(
            requires_clarification=True,
            clarification_question="Which app should I open?",
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("requires clarification" in error for error in result.errors)
        )

    def test_plan_containing_errors_is_invalid(self):
        plan = ActionPlan(
            errors=("Missing required recipient.",),
        )

        result = self.validator.validate(plan)

        self.assertFalse(result.is_valid)
        self.assertIn("Missing required recipient.", result.errors)
