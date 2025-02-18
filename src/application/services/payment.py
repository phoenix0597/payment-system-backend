import hashlib
from src.config.config import settings
from src.domain.models.payment import Payment
from src.infrastructure.repositories.payment import PaymentRepository
from src.infrastructure.repositories.account import AccountRepository
from src.api.v1.schemas.payment import WebhookPayload


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        account_repository: AccountRepository,
    ):
        self.payment_repository = payment_repository
        self.account_repository = account_repository

    @staticmethod
    def verify_signature(payload: WebhookPayload) -> bool:
        data = f"{payload.account_id}{payload.amount}{payload.transaction_id}{payload.user_id}{settings.WEBHOOK_SECRET_KEY}"
        calculated_signature = hashlib.sha256(data.encode()).hexdigest()
        return calculated_signature == payload.signature

    async def process_payment(self, payload: WebhookPayload) -> Payment:
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

        return payment
