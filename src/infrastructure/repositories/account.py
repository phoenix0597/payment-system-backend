from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models.account import Account
from src.infrastructure.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: AsyncSession):
        super().__init__(Account, session)

    async def get_by_user_id(self, user_id: int):
        return await self.get_by_filter(self.model.user_id == user_id)

    async def update_balance(self, account_id: int, amount: Decimal) -> Account:
        return await self.update(account_id, balance=self.model.balance + amount)
