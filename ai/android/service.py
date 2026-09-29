from ai.android.types import (
    AndroidActionRequest,
    AndroidActionResult,
)


class AndroidActionEngine:
    """
    Executes authorized Android actions through an injected executor.

    This engine does not decide whether an action is safe.
    """

    def __init__(self, executor):
        self.executor = executor

    def execute(
        self,
        request: AndroidActionRequest,
    ) -> AndroidActionResult:
        """
        Execute an Android action through the configured executor.
        """
        if not isinstance(request, AndroidActionRequest):
            raise TypeError(
                "request must be an AndroidActionRequest."
            )

        result = self.executor.execute(request)

        if not isinstance(result, AndroidActionResult):
            raise TypeError(
                "executor must return an AndroidActionResult."
            )

        return result