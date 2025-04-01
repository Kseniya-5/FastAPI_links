from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users import FastAPIUsers
from auth.database import User, get_async_session
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate, UserUpdate

# Транспорт для аутентификации (Cookie)
cookie_transport = CookieTransport(cookie_name="auth_token", cookie_max_age=3600)

# Стратегия аутентификации (JWT)
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret="SECRET", lifetime_seconds=3600)

# Бэкенд аутентификации
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# Инициализация FastAPIUsers
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Маршруты для регистрации
register_router = fastapi_users.get_register_router(UserRead, UserCreate)

# Маршруты для управления пользователями
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)