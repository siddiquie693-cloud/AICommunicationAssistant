class NIRACoreError(Exception):
    """
    Base exception for NIRA Core errors.
    """


class NIRACoreValidationError(NIRACoreError):
    """
    Raised when a NIRA Core input or output violates its contract.
    """


class NIRACoreProcessingError(NIRACoreError):
    """
    Raised when NIRA Core cannot complete request processing.
    """