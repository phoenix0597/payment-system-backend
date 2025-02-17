from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional

from src.api.v1.schemas.account import AccountInDB


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    id: int
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithAccounts(UserInDB):
    accounts: List["AccountInDB"]
