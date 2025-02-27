from decimal import Decimal
from typing import List, Optional

from src.infrastructure.repositories.account import AccountRepository
from src.api.v1.schemas.account import AccountCreate, AccountInDB
from src.application.services.cache import CacheService, get_cache_service
from src.core.logger import log


class AccountService:
    """
    Service class for managing accounts.

    This class provides methods for creating, retrieving, and updating accounts.

    Attributes:
        account_repository (AccountRepository): The repository for account data access.
    """

    def __init__(self, account_repository: AccountRepository):
        """
        Initialize the AccountService with the necessary dependencies.

        Args:
            account_repository (AccountRepository): The repository for account data access.
        """
        self.account_repository = account_repository
        self.cache_service: CacheService = get_cache_service()

    async def create_account(self, account_data: AccountCreate) -> AccountInDB:
        """
        Create a new account.

        Args:
            account_data (AccountCreate): The account data to create.

        Returns:
            AccountInDB: The created account.
        """
        account = await self.account_repository.create(**account_data.model_dump())
        account_schema = AccountInDB.model_validate(account)
        # инвалидация кэша для счетов пользователя
        await self.cache_service.delete(f"user:{account_schema.user_id}")
        log.info(f"Account created successfully for user_id: {account_data.user_id}")
        return account_schema

    async def get_account(self, account_id: int) -> Optional[AccountInDB]:
        """
        Retrieve an account by its ID.

        Args:
            account_id (int): The ID of the account to retrieve.

        Returns:
            Optional[AccountInDB]: The account if found, None otherwise.
        """
        account = await self.account_repository.get(account_id)
        return AccountInDB.model_validate(account) if account else None

    async def get_accounts_by_user_id(self, user_id: int) -> List[AccountInDB]:
        """
        Retrieve all accounts for a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            List[AccountInDB]: A list of accounts belonging to the user.
        """
        cache_key = f"accounts:user:{user_id}"
        cached_accounts = await self.cache_service.get(cache_key)
        if cached_accounts:
            log.debug(f"Cache hit for accounts of user_id: {user_id}")
            return [AccountInDB(**acc) for acc in cached_accounts]

        accounts = await self.account_repository.get_by_user_id(user_id)
        account_schemas = [AccountInDB.model_validate(acc) for acc in accounts]
        await self.cache_service.set(
            cache_key,
            [acc.model_dump() for acc in account_schemas],
            expire=settings.CACHE_TTL,
        )
        return account_schemas

    async def update_balance(self, account_id: int, amount: Decimal) -> AccountInDB:
        """
        Update the balance of an account.

        Args:
            account_id (int): The ID of the account.
            amount (Decimal): The amount to add to the balance.

        Returns:
            AccountInDB: The updated account.
        """
        current_balance = await self.account_repository.get_balance(account_id)
        new_balance = current_balance + amount
        if new_balance < 0:
            raise ValueError("Account balance cannot be negative")

        updated_account = await self.account_repository.update_balance(
            account_id, amount
        )
        account_schema = AccountInDB.model_validate(updated_account)
        # инвалидация кэша для счетов пользователя
        await self.cache_service.delete(f"user:{account_schema.user_id}")
        return account_schema

    async def get_balance(self, account_id: int) -> Decimal:
        """
        Get the balance of an account.

        Args:
            account_id (int): The ID of the account.

        Returns:
            Decimal: The balance of the account.
        """
        return await self.account_repository.get_balance(account_id)
