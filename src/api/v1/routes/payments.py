from fastapi import APIRouter, Depends, HTTPException
from src.api.deps import get_current_user, get_payment_service
from src.api.v1.schemas.payment import WebhookPayload, PaymentInDB
from src.application.services.payment import PaymentService

router = APIRouter()


@router.post("/webhook", response_model=PaymentInDB)
async def process_payment_webhook(
    payload: WebhookPayload,
    payment_service: PaymentService = Depends(get_payment_service),
):
    try:
        return await payment_service.process_payment(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my")
async def get_user_payments(
    current_user=Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    return await payment_service.get_user_payments(current_user.id)
