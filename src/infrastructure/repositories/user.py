from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models.user import User
from src.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str):
        query = select(User).where(User.email == email)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_accounts(self, user_id: int):
        query = select(User).where(User.id == user_id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalars().first()
