from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.user import UserInDB
from src.application.services.auth import AuthService
from src.application.services.payment import PaymentService
from src.config.config import settings
from src.application.services.user import UserService
from src.infrastructure.database import get_session
from src.application.services.base import ServiceFactory

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}{settings.TOKEN_URL}"
)
# print(f"{settings.API_PREFIX}{settings.TOKEN_URL}")

TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_services(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ServiceFactory:
    """Create and return service factory instance."""
    return ServiceFactory(session)


ServiceFactoryDep = Annotated[ServiceFactory, Depends(get_services)]


def raise_credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_service(services: ServiceFactoryDep) -> UserService:
    """Get user service instance."""
    return services.get_user_service()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserInDB:
    print(f"{token=}")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise raise_credentials_exception()
    except JWTError:
        raise raise_credentials_exception()

    user = await user_service.get_user(user_id)
    if user is None:
        raise raise_credentials_exception()
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


async def get_auth_service(services: ServiceFactoryDep) -> AuthService:
    return services.get_auth_service()


async def get_payment_service(services: ServiceFactoryDep) -> PaymentService:
    return services.get_payment_service()
