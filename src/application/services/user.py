from typing import Optional, List

from src.application.services.auth import AuthService
from src.infrastructure.repositories.user import UserRepository
from src.core.logger import log
from src.api.v1.schemas.user import UserCreate, UserUpdate, UserInDB, UserWithAccounts


class UserService:
    def __init__(self, user_repository: UserRepository, auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    async def create_user(self, user_data: UserCreate):
        """
        Create a new user.

        Args:
            user_data (UserCreate): The user data to create.

        Returns:
            UserInDB: The created user object
        """
        log.info(f"Creating user with email: {user_data.email}")
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        user = await self.user_repository.create(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )
        log.info(f"User {user.email} created successfully")
        return UserInDB.model_validate(user)

    async def update_user(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[UserInDB]:
        """
        Update a user's information.

        Args:
            user_id (int): The ID of the user to update.
            user_data (UserUpdate): The updated user data.

        Returns:
            Optional[UserInDB]: The updated user object if successful, otherwise None
        """
        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = self.auth_service.get_password_hash(
                update_data.pop("password")
            )
        updated_user = await self.user_repository.update(user_id, **update_data)
        return UserInDB.model_validate(updated_user) if updated_user else None

    async def delete_user(self, user_id: int):
        return await self.user_repository.delete(user_id)

    async def get_user(self, user_id: int) -> Optional[UserInDB]:
        """
        Get a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Optional[UserInDB]: The user object if found, otherwise None
        """
        user = await self.user_repository.get(user_id)
        return UserInDB.model_validate(user) if user else None

    async def get_users(self) -> List[UserWithAccounts]:
        """
        Get all users with their accounts.

        Returns:
            List[UserWithAccounts]: List of all users with their accounts
        """
        users = await self.user_repository.get_all_with_accounts()
        return [UserWithAccounts.model_validate(user) for user in users]
