from ai.core.service import NIRACore


def create_nira_core(
    brain,
) -> NIRACore:
    """
    Create the NIRA application core from a configured Brain.
    """
    return NIRACore(brain)