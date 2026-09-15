from abc import ABC, abstractmethod

class PhoneProvider(ABC):
    @abstractmethod
    def make_call(self, recipient: str, twiml: str):
        raise NotImplemented

    @abstractmethod
    def handle_incoming_call(self, payload: dict):
        raise NotImplementedError

    @abstractmethod
    def generate_call_response(self, text: str):
        raise NotImplementedError