from ai.brain.service import NIRABrain
from ai.core.service import NIRACore


def create_nira_core(
    brain=None,
    *,
    ai_service=None,
) -> NIRACore:
    """
    Create the NIRA application core.

    If a Brain is supplied, it is used directly.
    Otherwise, a Brain is created from the supplied AI service.
    """
    if brain is None:
        if ai_service is None:
            raise ValueError(
                "Either brain or ai_service must be provided."
            )

        brain = NIRABrain(ai_service)

    return NIRACore(brain)