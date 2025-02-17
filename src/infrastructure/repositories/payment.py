from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models.payment import Payment
from src.infrastructure.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_transaction_id(self, transaction_id: str):
        query = select(Payment).where(Payment.transaction_id == transaction_id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_user_id(self, user_id: int):
        query = select(Payment).where(Payment.user_id == user_id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().all()
