from fastapi import Depends
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from auth.database import User, get_user_db

SECRET = "SECRET"  # Секретный ключ для UserManager


class UserManager(UUIDIDMixin, BaseUserManager[User, int]):
    """
    Менеджер пользователей для FastAPI-Users.
    """
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request=None):
        """
        Действие после регистрации пользователя.
        """
        print(f"Пользователь {user.id} успешно зарегистрирован.")

    async def on_after_forgot_password(self, user: User, token: str, request=None):
        """
        Действие после запроса на сброс пароля.
        """
        print(f"Ссылка для сброса пароля отправлена пользователю {user.id}. Токен: {token}")

    async def on_after_request_verify(self, user: User, token: str, request=None):
        """
        Действие после запроса верификации пользователя.
        """
        print(f"Ссылка для верификации отправлена пользователю {user.id}. Токен: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    """
    Возвращает экземпляр UserManager для работы с пользователями.
    """
    yield UserManager(user_db)