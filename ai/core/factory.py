
from ai.brain.service import NIRABrain
from ai.core.dependencies import NIRADependencies
from ai.core.service import NIRACore


def create_nira_core(
    brain=None,
    *,
    ai_service=None,
    dependencies: NIRADependencies | None = None,
) -> NIRACore:
    """
    Create the NIRA application core.

    Supports:
    1. An existing Brain instance.
    2. An AI service for backward compatibility.
    3. An explicit NIRADependencies configuration.
    """

    if dependencies is not None:
        if brain is not None or ai_service is not None:
            raise ValueError(
                "Provide dependencies separately from brain or ai_service."
            )

        if not isinstance(dependencies, NIRADependencies):
            raise TypeError(
                "dependencies must be a NIRADependencies instance."
            )

        dependencies.validate_for_brain()

        brain = NIRABrain(
            dependencies.ai_service,
            **dependencies.get_brain_kwargs(),
        )

    elif brain is None:
        if ai_service is None:
            raise ValueError(
                "Either brain, ai_service, or dependencies "
                "must be provided."
            )

        brain = NIRABrain(ai_service)

    return NIRACore(brain)