import hashlib
from decimal import Decimal
from typing import Optional, List

from src.application.services.cache import CacheService, get_cache_service
from src.config.config import settings
from src.infrastructure.repositories.payment import PaymentRepository
from src.infrastructure.repositories.account import AccountRepository
from src.api.v1.schemas.payment import WebhookPayload, PaymentInDB
from src.core.logger import log


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
        self.cache_service: CacheService = get_cache_service()

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

        is_valid = calculated_signature == payload.signature
        log.debug(f"Signature verification: {'valid' if is_valid else 'invalid'}")

        # FOR DEBUGGING
        print(f"{data=}")
        print(f"{calculated_signature=}")

        return is_valid

    async def _get_or_create_account(self, account_id: int, user_id: int) -> int:
        """
        Get an existing account ID if it belongs to the user, otherwise create a new one.

        Args:
            account_id (int): The account ID from the payload.
            user_id (int): The user ID from the payload.

        Returns:
            int: The account ID to use for the payment.
        """
        account = await self.account_repository.get(account_id)
        if account and account.user_id == user_id:
            return account.id
        # Если счет не существует или принадлежит другому пользователю, создаем новый
        log.info(f"Creating new account for user_id: {user_id}")
        new_account = await self.account_repository.create(user_id=user_id)
        return new_account.id

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
        log.info(f"Processing payment with transaction_id: {payload.transaction_id}")
        if not self.verify_signature(payload):
            log.error(f"Invalid signature for transaction_id: {payload.transaction_id}")
            raise ValueError("Invalid signature")

        existing_payment = await self.payment_repository.get_by_transaction_id(
            payload.transaction_id,
        )
        if existing_payment:
            log.warning(f"Duplicate transaction_id: {payload.transaction_id}")
            raise ValueError("Transaction already processed")

        account_id = await self._get_or_create_account(
            payload.account_id, payload.user_id
        )

        payment = await self.payment_repository.create(
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            account_id=account_id,
            amount=payload.amount,
        )

        await self.account_repository.update_balance(account_id, payload.amount)
        payment_schema = PaymentInDB.model_validate(payment)

        # Кэшируем отдельный платеж и инвалидируем список платежей пользователя
        await self.cache_service.set(
            f"payment:{payment.id}", payment_schema.model_dump()
        )
        await self.cache_service.delete(f"payments:user:{payload.user_id}")
        log.info(
            f"Payment processed successfully for transaction_id: {payment.transaction_id}"
        )
        return payment_schema

    async def get_payment(self, payment_id: int) -> Optional[PaymentInDB]:
        """
        Retrieve a payment by its ID.

        Args:
            payment_id (int): The ID of the payment to retrieve.

        Returns:
            Optional[PaymentInDB]: The payment if found, None otherwise.
        """
        cache_key = f"payment:{payment_id}"
        cached_payment = await self.cache_service.get(cache_key)
        if cached_payment:
            log.debug(f"Cache hit for payment {payment_id}")
            return PaymentInDB(**cached_payment)

        payment = await self.payment_repository.get(payment_id)
        if payment:
            payment_schema = PaymentInDB.model_validate(payment)
            await self.cache_service.set(cache_key, payment_schema.model_dump())
            return payment_schema
        return None

    async def get_payments_by_user_id(self, user_id: int) -> List[PaymentInDB]:
        """
        Retrieve all payments for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            List[PaymentInDB]: A list of payments belonging to the user.
        """
        payments = await self.payment_repository.get_by_user_id(user_id)
        payment_schemas = [PaymentInDB.model_validate(payment) for payment in payments]
        log.info(f"Retrieved {len(payment_schemas)} payments for user_id: {user_id}")
        return payment_schemas

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
        total = sum((payment.amount for payment in payments), Decimal("0"))
        log.debug(f"Total payments amount for user with user_id: {user_id} is: {total}")
        return total
