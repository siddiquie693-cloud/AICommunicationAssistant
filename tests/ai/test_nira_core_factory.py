from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.core.factory import create_nira_core
from ai.core.service import NIRACore
from ai.brain.service import NIRABrain

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

        self.assertIsInstance(
            core,
            NIRACore,
        )

        self.assertIsInstance(
            core.brain,
            NIRABrain,
        )

        self.assertIs(
            core.brain.ai_service,
            ai_service,
        )    

    def test_create_nira_core_requires_brain_or_ai_service(self):
        with self.assertRaises(ValueError):
            create_nira_core()    