from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models.user import User
from src.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str):
        return await self.get_one_by_filter(self.model.email == email)

    async def get_with_accounts(self, user_id: int):
        return await self.get(user_id)
