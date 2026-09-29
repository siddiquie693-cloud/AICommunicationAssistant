from django.test import SimpleTestCase

from ai.core.exceptions import (
    NIRACoreError,
    NIRACoreProcessingError,
    NIRACoreValidationError,
)


class NIRACoreExceptionTests(SimpleTestCase):

    def test_nira_core_validation_error_inherits_from_core_error(self):
        self.assertTrue(
            issubclass(
                NIRACoreValidationError,
                NIRACoreError,
            )
        )

    def test_nira_core_processing_error_inherits_from_core_error(self):
        self.assertTrue(
            issubclass(
                NIRACoreProcessingError,
                NIRACoreError,
            )
        )

    def test_nira_core_errors_can_store_error_message(self):
        error = NIRACoreProcessingError(
            "Core processing failed."
        )

        self.assertEqual(
            str(error),
            "Core processing failed.",
        )