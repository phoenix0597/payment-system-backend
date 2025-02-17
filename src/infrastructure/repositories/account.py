from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models.account import Account
from src.infrastructure.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: AsyncSession):
        super().__init__(Account, session)

    async def get_by_user_id(self, user_id: int):
        query = select(Account).where(Account.user_id == user_id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_balance(self, account_id: int, amount: Decimal) -> Account:
        account = await self.get(account_id)
        if account:
            account.balance += amount
            await self.session.commit()
            await self.session.refresh(account)
        return account
