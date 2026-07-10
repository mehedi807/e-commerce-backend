from abc import ABC, abstractmethod
from orders.models import Order


class PaymentProvider(ABC):
    @abstractmethod
    def initiate_payment(self, *, order: Order) -> dict:
        pass

    @abstractmethod
    def confirm_payment(self, *, transaction_id: str) -> str:
        pass

    @abstractmethod
    def handle_webhook(self, *, payload: bytes, headers: dict) -> dict:
        pass

