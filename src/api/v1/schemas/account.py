from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class AccountBase(BaseModel):
    user_id: int


class AccountCreate(AccountBase):
    pass


class AccountInDB(AccountBase):
    id: int
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)
