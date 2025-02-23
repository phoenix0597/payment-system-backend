from fastapi import APIRouter, Depends
from typing import List
from src.api.deps import get_current_user, get_services
from src.api.v1.schemas.account import AccountInDB
from src.api.v1.schemas.user import UserInDB
from src.application.services.account import AccountService

router = APIRouter()


def get_account_service(services=Depends(get_services)) -> AccountService:
    return services.get_account_service()


@router.get("/me", response_model=List[AccountInDB])
async def get_user_accounts(
    current_user: UserInDB = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
):
    """Get all accounts of the current user."""
    return await account_service.get_accounts_by_user_id(current_user.id)
