from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime


class WebhookPayload(BaseModel):
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    signature: str


class PaymentInDB(BaseModel):
    id: int
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
