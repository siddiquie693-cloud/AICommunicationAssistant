
from unittest.mock import Mock
from ai.safety.service import SafetyEngine

from django.test import SimpleTestCase
from ai.safety.evaluator import RuleBasedSafetyEvaluator
from ai.brain.service import NIRABrain
from ai.brain.types import BrainRequest
from ai.core.dependencies import NIRADependencies
from ai.core.factory import create_nira_core
from ai.core.service import NIRACore


class NIRACoreFactoryTests(SimpleTestCase):

    def test_create_nira_core_returns_configured_core(self):
        brain = Mock()

        core = create_nira_core(brain)

        self.assertIsInstance(core, NIRACore)
        self.assertIs(core.brain, brain)

    def test_create_nira_core_creates_brain_from_ai_service(self):
        ai_service = Mock()

        core = create_nira_core(
            ai_service=ai_service,
        )

        self.assertIsInstance(core, NIRACore)
        self.assertIsInstance(core.brain, NIRABrain)
        self.assertIs(core.brain.ai_service, ai_service)

    def test_create_nira_core_creates_brain_from_dependencies(self):
        ai_service = Mock()
        context_engine = Mock()
        intent_engine = Mock()
        action_planner = Mock()
        safety_engine = Mock()
        android_action_engine = Mock()
        person_identity_resolver = Mock()
        safety_request_builder = Mock()

        dependencies = NIRADependencies(
            ai_service=ai_service,
            context_engine=context_engine,
            intent_engine=intent_engine,
            action_planner=action_planner,
            safety_engine=safety_engine,
            android_action_engine=android_action_engine,
            person_identity_resolver=person_identity_resolver,
            safety_request_builder=safety_request_builder,
        )

        core = create_nira_core(
            dependencies=dependencies,
        )

        self.assertIsInstance(core, NIRACore)
        self.assertIsInstance(core.brain, NIRABrain)

        self.assertIs(core.brain.ai_service, ai_service)
        self.assertIs(core.brain.context_engine, context_engine)
        self.assertIs(core.brain.intent_engine, intent_engine)
        self.assertIs(core.brain.action_planner, action_planner)
        self.assertIs(core.brain.safety_engine, safety_engine)
        self.assertIs(
            core.brain.android_action_engine,
            android_action_engine,
        )
        self.assertIs(
            core.brain.person_identity_resolver,
            person_identity_resolver,
        )

    def test_create_nira_core_rejects_incomplete_dependencies(self):
        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=None,
            action_planner=Mock(),
            safety_engine=Mock(),
        )

        with self.assertRaises(ValueError):
            create_nira_core(dependencies=dependencies)

    def test_create_nira_core_rejects_invalid_dependencies_type(self):
        with self.assertRaises(TypeError):
            create_nira_core(dependencies=Mock())

    def test_create_nira_core_rejects_mixed_dependency_arguments(self):
        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=Mock(),
            action_planner=Mock(),
            safety_engine=Mock(),
        )

        with self.assertRaises(ValueError):
            create_nira_core(
                dependencies=dependencies,
                ai_service=Mock(),
            )

    def test_create_nira_core_requires_brain_or_ai_service(self):
        with self.assertRaises(ValueError):
            create_nira_core()

    def test_create_nira_core_integrates_with_brain_pipeline(self):
        ai_service = Mock()

        core = create_nira_core(
            ai_service=ai_service,
        )

        request = BrainRequest(
            text="Open calculator",
        )

        with self.assertRaises(ValueError):
            core.process(request)

    def test_create_nira_core_builds_safety_engine_from_evaluator(self):
        evaluator = RuleBasedSafetyEvaluator()

        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=Mock(),
            action_planner=Mock(),
            safety_evaluator=evaluator,
        )

        core = create_nira_core(dependencies=dependencies)

        self.assertIsInstance(core.brain.safety_engine, SafetyEngine)
        self.assertIs(
            core.brain.safety_engine.evaluator,
            evaluator,
        )


class NIRADependenciesTests(SimpleTestCase):

    def test_validate_for_phone_actions_requires_android_engine(self):
        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=Mock(),
            action_planner=Mock(),
            safety_engine=Mock(),
        )

        with self.assertRaises(ValueError):
            dependencies.validate_for_phone_actions()

    def test_validate_for_brain_requires_safety_dependency(self):
        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=Mock(),
            action_planner=Mock(),
        )

        with self.assertRaises(ValueError):
            dependencies.validate_for_brain()

    def test_validate_for_brain_rejects_both_safety_dependencies(self):
        dependencies = NIRADependencies(
            ai_service=Mock(),
            context_engine=Mock(),
            intent_engine=Mock(),
            action_planner=Mock(),
            safety_engine=Mock(),
            safety_evaluator=Mock(),
        )

        with self.assertRaises(ValueError):
            dependencies.validate_for_brain()
