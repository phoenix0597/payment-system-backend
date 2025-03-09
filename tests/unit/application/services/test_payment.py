# tests/unit/application/services/test_payment.py
import pytest
from decimal import Decimal
import hashlib
from datetime import datetime
from src.application.services.payment import PaymentService
from src.api.v1.schemas.payment import WebhookPayload, PaymentInDB
from src.config.config import settings


@pytest.fixture
def sample_payment():
    return PaymentInDB(
        id=1,
        transaction_id="test123",
        user_id=1,
        account_id=1,
        amount=Decimal("100.50"),
        created_at=datetime.now(),
    )


@pytest.fixture
def valid_webhook_payload():
    user_id = 1
    account_id = 1
    amount = Decimal("100.50")
    transaction_id = "test123"

    # Создаем подпись как в сервисе
    data = f"{account_id}{amount}{transaction_id}{user_id}{settings.WEBHOOK_SECRET_KEY}"
    signature = hashlib.sha256(data.encode()).hexdigest()

    return WebhookPayload(
        transaction_id=transaction_id,
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        signature=signature,
    )


@pytest.mark.asyncio
async def test_verify_signature_valid(mocker, valid_webhook_payload):
    # Arrange
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()
    payment_service = PaymentService(mock_payment_repo, mock_account_repo)

    # Act
    result = payment_service.verify_signature(valid_webhook_payload)

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_verify_signature_invalid(mocker, valid_webhook_payload):
    # Arrange
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()
    payment_service = PaymentService(mock_payment_repo, mock_account_repo)

    # Изменяем подпись для невалидности
    valid_webhook_payload.signature = "invalid_signature"

    # Act
    result = payment_service.verify_signature(valid_webhook_payload)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_process_payment_success(mocker, valid_webhook_payload, sample_payment):
    # Arrange
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()
    mock_cache_service = mocker.AsyncMock()

    # Настраиваем моки
    mock_payment_repo.get_by_transaction_id.return_value = None
    mock_account_repo.get.return_value = None
    mock_account_repo.create.return_value = mocker.Mock(
        id=valid_webhook_payload.account_id
    )
    mock_payment_repo.create.return_value = sample_payment

    payment_service = PaymentService(mock_payment_repo, mock_account_repo)
    payment_service.cache_service = mock_cache_service

    # Act
    result = await payment_service.process_payment(valid_webhook_payload)

    # Assert
    assert result.id == sample_payment.id
    assert result.transaction_id == valid_webhook_payload.transaction_id
    assert result.amount == valid_webhook_payload.amount

    # Проверяем, что методы были вызваны
    mock_payment_repo.get_by_transaction_id.assert_called_once_with(
        valid_webhook_payload.transaction_id
    )
    mock_account_repo.create.assert_called_once()
    mock_payment_repo.create.assert_called_once()
    mock_account_repo.update_balance.assert_called_once_with(
        valid_webhook_payload.account_id, valid_webhook_payload.amount
    )
    mock_cache_service.set.assert_called_once()
    mock_cache_service.delete.assert_called_once()


@pytest.mark.asyncio
async def test_process_payment_duplicate_transaction(
    mocker, valid_webhook_payload, sample_payment
):
    # Arrange
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()

    # Настраиваем мок для имитации существующей транзакции
    mock_payment_repo.get_by_transaction_id.return_value = sample_payment

    payment_service = PaymentService(mock_payment_repo, mock_account_repo)

    # Act & Assert
    with pytest.raises(ValueError, match="Transaction already processed"):
        await payment_service.process_payment(valid_webhook_payload)

    # Проверяем, что был только запрос на проверку существующей транзакции
    mock_payment_repo.get_by_transaction_id.assert_called_once_with(
        valid_webhook_payload.transaction_id
    )
    mock_account_repo.create.assert_not_called()
    mock_payment_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_payments_by_user_id_cache_hit(mocker):
    # Arrange
    user_id = 1
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()
    mock_cache_service = mocker.AsyncMock()

    # Настраиваем мок кэша для имитации кэш-хита
    cached_payments = [
        {
            "id": 1,
            "transaction_id": "tx1",
            "user_id": user_id,
            "account_id": 1,
            "amount": "100.50",
            "created_at": "2023-01-01T12:00:00",
        }
    ]
    mock_cache_service.get.return_value = cached_payments

    payment_service = PaymentService(mock_payment_repo, mock_account_repo)
    payment_service.cache_service = mock_cache_service

    # Act
    result = await payment_service.get_payments_by_user_id(user_id)

    # Assert
    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].transaction_id == "tx1"
    assert result[0].amount == Decimal("100.50")

    # Проверяем, что кэш был запрошен, но репозиторий - нет
    mock_cache_service.get.assert_called_once_with(f"payments:user:{user_id}")
    mock_payment_repo.get_by_user_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_payments_by_user_id_cache_miss(mocker, sample_payment):
    # Arrange
    user_id = 1
    mock_payment_repo = mocker.AsyncMock()
    mock_account_repo = mocker.AsyncMock()
    mock_cache_service = mocker.AsyncMock()

    # Настраиваем моки
    mock_cache_service.get.return_value = None
    mock_payment_repo.get_by_user_id.return_value = [sample_payment]

    payment_service = PaymentService(mock_payment_repo, mock_account_repo)
    payment_service.cache_service = mock_cache_service

    # Act
    result = await payment_service.get_payments_by_user_id(user_id)

    # Assert
    assert len(result) == 1
    assert result[0].id == sample_payment.id
    assert result[0].transaction_id == sample_payment.transaction_id

    # Проверяем, что был запрос к кэшу, а потом к репозиторию
    mock_cache_service.get.assert_called_once_with(f"payments:user:{user_id}")
    mock_payment_repo.get_by_user_id.assert_called_once_with(user_id)
    mock_cache_service.set.assert_called_once()
