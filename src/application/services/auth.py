from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

from src.api.v1.schemas.user import UserInDB
from src.config.config import settings
from src.core.logger import log
from src.infrastructure.repositories.user import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            Optional[UserInDB]: Authenticated user or None
        """
        log.info(f"Authenticating user with email: {email}")
        user = await self.user_repository.get_by_email(email)
        if not user:
            log.warning(f"Authentication failed: user not found with email: {email}")
            return None
        if not self.verify_password(password, user.hashed_password):
            log.warning(f"Authentication failed: invalid password for email: {email}")
            return None
        log.info(f"User authenticated successfully with email: {email}")
        return UserInDB.model_validate(user)

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data
            expires_delta: Optional expiration time

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        log.debug(f"Created access token for user_id: {data.get('sub')}")
        return encoded_jwt
