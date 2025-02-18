from decimal import Decimal
from typing import List, Optional

from src.infrastructure.repositories.account import AccountRepository
from src.api.v1.schemas.account import AccountCreate, AccountInDB


class AccountService:

    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    async def create_account(self, account_data: AccountCreate) -> AccountInDB:
        account = await self.account_repository.create(**account_data.model_dump())
        return AccountInDB.model_validate(account)

    async def get_account(self, account_id: int) -> Optional[AccountInDB]:
        account = await self.account_repository.get(account_id)
        return AccountInDB.model_validate(account) if account else None

    async def get_accounts_by_user_id(self, user_id: int) -> List[AccountInDB]:
        accounts = await self.account_repository.get_by_user_id(user_id)
        return [AccountInDB.model_validate(account) for account in accounts]

    async def update_balance(self, account_id: int, amount: Decimal) -> AccountInDB:

        current_balance = await self.account_repository.get_balance(account_id)
        new_balance = current_balance + amount
        if new_balance < 0:
            raise ValueError("Account balance cannot be negative")

        updated_account = await self.account_repository.update_balance(
            account_id, amount
        )
        return AccountInDB.model_validate(updated_account)

    async def get_balance(self, account_id: int) -> Decimal:
        return await self.account_repository.get_balance(account_id)
