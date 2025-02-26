from fastapi import APIRouter, Depends, HTTPException
from src.api.deps import get_current_user, get_payment_service
from src.api.v1.schemas.payment import WebhookPayload, PaymentInDB
from src.application.services.payment import PaymentService
from src.core.logger import log

router = APIRouter()


@router.post("/webhook", response_model=PaymentInDB)
async def process_payment_webhook(
    payload: WebhookPayload,
    payment_service: PaymentService = Depends(get_payment_service),
):
    log.info(f"Received webhook for transaction_id: {payload.transaction_id}")
    try:
        result = await payment_service.process_payment(payload)
        log.info(
            f"Webhook processed successfully for transaction_id: {payload.transaction_id}"
        )
        return result
    except ValueError as e:
        log.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my")
async def get_user_payments(
    current_user=Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    log.info(f"Fetching payments for user_id: {current_user.id}")
    return await payment_service.get_payments_by_user_id(current_user.id)
