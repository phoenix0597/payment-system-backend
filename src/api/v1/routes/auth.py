from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.config.config import settings
from src.api.deps import get_auth_service, raise_credentials_exception
from src.application.services.auth import AuthService

router = APIRouter()


@router.post(
    "/token",
    summary="Login and get access token",
    description="""Authenticate with email and password to receive a JWT token.

This token is only for use in external tools like curl or Postman 
by adding it to the 'Authorization: Bearer <token>' header.

For use access token in Swagger UI, enter your email and password in the 'Authorize' form,
and it will be automatically applied to protected endpoints.""",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email and password to receive a JWT token.

    To use this token in Swagger UI, enter your email and password in the 'Authorize' form,
    and it will be automatically applied to protected endpoints. If you obtain the token
    manually via this endpoint (e.g., using 'Try it out'), use it in external tools like
    curl or Postman by adding it to the 'Authorization: Bearer <token>' header."""

    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise raise_credentials_exception()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
