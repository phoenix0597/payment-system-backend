# tests/unit/application/services/test_auth.py
import pytest
from src.application.services.auth import AuthService
from src.domain.models import User
from src.infrastructure.repositories.user import UserRepository
from src.api.v1.schemas.user import UserInDB


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, expected_user",
    [
        # Сценарий 1: Успешная аутентификация
        (
            "test@example.com",
            "password",
            UserInDB(
                id=1,
                email="test@example.com",  # noqa
                full_name="Test User",
                is_admin=False,
            ),
        ),
        # Сценарий 2: Неверный пароль
        (
            "test@example.com",
            "wrong_password",
            None,
        ),
    ],
    ids=["success", "invalid_password"],  # Имена для сценариев в отчете
)
async def test_authenticate_user(mocker, email, password, expected_user):
    # Arrange
    mock_user_repo = mocker.AsyncMock(spec=UserRepository)
    mock_user = mocker.Mock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.is_admin = False
    mock_user.hashed_password = AuthService.get_password_hash("password")
    mock_user_repo.get_by_email.return_value = mock_user
    auth_service = AuthService(mock_user_repo)

    # Act
    result = await auth_service.authenticate_user(email, password)

    # Assert
    if expected_user is not None:
        # Для успешного сценария сравниваем результат с ожидаемым пользователем
        assert result == expected_user
    else:
        # Для неуспешного сценария проверяем, что возвращается None
        assert result is None
    mock_user_repo.get_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_authenticate_user_user_not_found(mocker):
    # Arrange
    mock_user_repo = mocker.AsyncMock(spec=UserRepository)
    mock_user_repo.get_by_email.return_value = None
    auth_service = AuthService(mock_user_repo)

    # Act
    result = await auth_service.authenticate_user("test@example.com", "password")

    # Assert
    assert result is None
    mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
