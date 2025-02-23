import hashlib
from decimal import Decimal
from typing import Optional, List

from src.config.config import settings
from src.infrastructure.repositories.payment import PaymentRepository
from src.infrastructure.repositories.account import AccountRepository
from src.api.v1.schemas.payment import WebhookPayload, PaymentInDB


class PaymentService:
    """
    Service class for managing payment-related operations.

    This class provides methods for processing payments and retrieving payment information.

    Attributes:
        payment_repository (PaymentRepository): The repository for payment data access.
        account_repository (AccountRepository): The repository for account data access.
    """

    def __init__(
        self,
        payment_repository: PaymentRepository,
        account_repository: AccountRepository,
    ):
        """
        Initialize the PaymentService with the necessary dependencies.

        Args:
            payment_repository (PaymentRepository): The repository for payment data access.
            account_repository (AccountRepository): The repository for account data access.
        """
        self.payment_repository = payment_repository
        self.account_repository = account_repository

    @staticmethod
    def verify_signature(payload: WebhookPayload) -> bool:
        """
        Verify the signature of a webhook payload.

        Args:
            payload (WebhookPayload): The webhook payload to verify.

        Returns:
            bool: True if the signature is valid, False otherwise.
        """
        data = f"{payload.account_id}{payload.amount}{payload.transaction_id}{payload.user_id}{settings.WEBHOOK_SECRET_KEY}"
        calculated_signature = hashlib.sha256(data.encode()).hexdigest()
        return calculated_signature == payload.signature

    async def process_payment(self, payload: WebhookPayload) -> PaymentInDB:
        """
        Process a payment from a webhook payload.

        Args:
            payload (WebhookPayload): The webhook payload containing payment information.

        Returns:
            PaymentInDB: The processed payment.

        Raises:
            ValueError: If the signature is invalid or the transaction has already been processed.
        """
        if not self.verify_signature(payload):
            raise ValueError("Invalid signature")

        existing_payment = await self.payment_repository.get_by_transaction_id(
            payload.transaction_id
        )
        if existing_payment:
            raise ValueError("Transaction already processed")

        account = await self.account_repository.get(payload.account_id)
        if not account:
            account = await self.account_repository.create(user_id=payload.user_id)

        payment = await self.payment_repository.create(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            account_id=account.id,
            amount=payload.amount,
        )

        await self.account_repository.update_balance(account.id, payload.amount)

        return PaymentInDB.model_validate(payment)

    async def get_payment(self, payment_id: int) -> Optional[PaymentInDB]:
        """
        Retrieve a payment by its ID.

        Args:
            payment_id (int): The ID of the payment to retrieve.

        Returns:
            Optional[PaymentInDB]: The payment if found, None otherwise.
        """
        payment = await self.payment_repository.get(payment_id)
        return PaymentInDB.model_validate(payment) if payment else None

    async def get_payments_by_user_id(self, user_id: int) -> List[PaymentInDB]:
        """
        Retrieve all payments for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            List[PaymentInDB]: A list of payments belonging to the user.
        """
        payments = await self.payment_repository.get_by_user_id(user_id)
        return [PaymentInDB.model_validate(payment) for payment in payments]

    async def get_payment_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[PaymentInDB]:
        """
        Retrieve a payment by its transaction ID.

        Args:
            transaction_id (str): The transaction ID of the payment to retrieve.

        Returns:
            Optional[PaymentInDB]: The payment if found, None otherwise.
        """
        payment = await self.payment_repository.get_by_transaction_id(transaction_id)
        return PaymentInDB.model_validate(payment) if payment else None

    async def get_total_payments_amount(self, user_id: int) -> Decimal:
        """
        Calculate the total amount of payments for a user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Decimal: The total amount of payments.
        """
        payments = await self.get_payments_by_user_id(user_id)
        return sum((payment.amount for payment in payments), Decimal("0"))
