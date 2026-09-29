from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.core.factory import create_nira_core
from ai.core.service import NIRACore


class NIRACoreFactoryTests(SimpleTestCase):

    def test_create_nira_core_returns_configured_core(self):
        brain = Mock()

        core = create_nira_core(brain)

        self.assertIsInstance(core, NIRACore)
        self.assertIs(core.brain, brain)