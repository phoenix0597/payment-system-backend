from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.models.user import User
from src.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str):
        return await self.get_one_by_filter(self.model.email == email)

    async def get_with_accounts(self, user_id: int):
        return await self.get(user_id)

    async def get_all_with_accounts(self) -> List[User]:
        query = select(self.model).options(selectinload(self.model.accounts))
        result = await self.session.execute(query)
        return list(result.scalars().all())
