from src.application.services.auth import AuthService
from src.infrastructure.repositories.user import UserRepository
from src.api.v1.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repository: UserRepository, auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def create_user(self, user_data: UserCreate):
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        user = await self.user_repository.create(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate):
        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = self.auth_service.get_password_hash(
                update_data.pop("password")
            )
        return await self.user_repository.update(user_id, **update_data)

    async def delete_user(self, user_id: int):
        return await self.user_repository.delete(user_id)

    async def get_user(self, user_id: int):
        return await self.user_repository.get(user_id)

    async def get_users(self):
        return await self.user_repository.get_all()
