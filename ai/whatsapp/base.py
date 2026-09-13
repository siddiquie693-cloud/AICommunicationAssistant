from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    @abstractmethod
    def send_message(
        self,
        recipient: str,
        message: str,
    ):
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
    ):
        raise NotImplementedError

    @abstractmethod
    def parse_webhook_message(
        self,
        payload: dict,
    ):
        raise NotImplementedError