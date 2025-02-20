from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.account import AccountService
from src.application.services.auth import AuthService
from src.application.services.payment import PaymentService
from src.application.services.user import UserService
from src.infrastructure.repositories.account import AccountRepository
from src.infrastructure.repositories.payment import PaymentRepository
from src.infrastructure.repositories.user import UserRepository


class ServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.account_repo = AccountRepository(session)
        self.payment_repo = PaymentRepository(session)

    def get_user_service(self) -> UserService:
        auth_service = AuthService(self.user_repo)
        return UserService(self.user_repo, auth_service)

    def get_auth_service(self) -> AuthService:
        return AuthService(self.user_repo)

    def get_account_service(self) -> AccountService:
        return AccountService(self.account_repo)

    def get_payment_service(self) -> PaymentService:
        return PaymentService(self.payment_repo, self.account_repo)
