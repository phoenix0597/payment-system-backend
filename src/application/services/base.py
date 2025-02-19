from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.account import AccountService
from src.application.services.auth import AuthService
from src.application.services.payment import PaymentService
from src.application.services.user import UserService
from src.infrastructure.database import get_session
from src.infrastructure.repositories.account import AccountRepository
from src.infrastructure.repositories.payment import PaymentRepository
from src.infrastructure.repositories.user import UserRepository


class ServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session

    def get_user_service(self) -> UserService:
        user_repo = UserRepository(self.session)
        auth_service = AuthService(user_repo)
        return UserService(user_repo, auth_service)

    def get_auth_service(self):
        user_repo = UserRepository(self.session)
        return AuthService(user_repo)

    def get_account_service(self) -> AccountService:
        account_repo = AccountRepository(self.session)
        return AccountService(account_repo)

    def get_payment_service(self) -> PaymentService:
        payment_repo = PaymentRepository(self.session)
        account_repo = AccountRepository(self.session)
        return PaymentService(payment_repo, account_repo)
