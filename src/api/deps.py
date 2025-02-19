from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.user import UserInDB
from src.application.services.account import AccountService
from src.config.config import settings
from src.infrastructure.database import get_session
from src.infrastructure.repositories.user import UserRepository
from src.infrastructure.repositories.account import AccountRepository
from src.infrastructure.repositories.payment import PaymentRepository
from src.application.services.auth import AuthService
from src.application.services.user import UserService
from src.application.services.payment import PaymentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Define app dependencies to make the code more clen
SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_user_service(session: SessionDep):
    """
    Create and return a UserService instance with its dependencies.
    """
    user_repo = UserRepository(session)
    auth_service = AuthService(user_repo)
    return UserService(user_repo, auth_service)


def get_auth_service(session: SessionDep):
    """
    Create and return an AuthService instance with its dependencies.
    """
    user_repo = UserRepository(session)
    return AuthService(user_repo)


def get_payment_service(session: SessionDep):
    """
    Create and return a PaymentService instance with its dependencies.
    """
    payment_repo = PaymentRepository(session)
    account_repo = AccountRepository(session)
    return PaymentService(payment_repo, account_repo)


def get_account_service(session: SessionDep):
    """
    Create and return an AccountService instance with its dependencies.
    """
    account_repo = AccountRepository(session)
    return AccountService(account_repo)


async def get_current_user(
    token: TokenDep,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserInDB:
    """
    Get the current authenticated user based on the JWT token.

    Args:
        token: JWT token from the request
        user_service: Instance of UserService for user operations

    Returns:
        User: The current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
