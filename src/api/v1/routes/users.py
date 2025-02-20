from typing import List
from fastapi import APIRouter, Depends, HTTPException
from src.api.deps import get_current_user, get_current_admin, get_user_service
from src.api.v1.schemas.user import UserCreate, UserUpdate, UserInDB, UserWithAccounts
from src.application.services.user import UserService

router = APIRouter()


@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user


@router.get("", response_model=List[UserWithAccounts])
async def read_users(
    current_user=Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_users()


@router.post("", response_model=UserInDB)
async def create_user(
    user: UserCreate,
    current_user=Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.create_user(user)


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user: UserUpdate,
    current_user=Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    updated_user = await user_service.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    if not await user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
