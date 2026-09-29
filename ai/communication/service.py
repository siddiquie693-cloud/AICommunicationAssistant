from ai.communication.types import (
    CommunicationRequest,
    CommunicationResult,
)


class CommunicationEngine:
    """
    Coordinates communication operations through an injected adapter.

    The engine does not directly access WhatsApp, SMS, phone,
    or Android APIs.
    """

    def __init__(self, adapter):
        self.adapter = adapter

    def send(
        self,
        request: CommunicationRequest,
    ) -> CommunicationResult:
        """
        Send a communication request through the configured adapter.
        """
        if not isinstance(request, CommunicationRequest):
            raise TypeError(
                "request must be a CommunicationRequest."
            )

        result = self.adapter.send(request)

        if not isinstance(result, CommunicationResult):
            raise TypeError(
                "adapter must return a CommunicationResult."
            )

        return result