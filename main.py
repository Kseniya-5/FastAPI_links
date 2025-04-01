import asyncio
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from auth.database import User, create_db_and_tables, get_async_session, LinkManager
from auth.auth import register_router, users_router, auth_backend, fastapi_users  # Импортируем fastapi_users
from auth.schemas import LinkCreate, LinkResponse, LinkStatsResponse, LinkSearch
from datetime import datetime
from auth.database import deleteExpiredLinks
import uvicorn

app = FastAPI()

# Маршруты для аутентификации
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Маршруты для регистрации
app.include_router(register_router, prefix="/auth", tags=["auth"])

# Маршруты для управления пользователями
app.include_router(users_router, prefix="/users", tags=["users"])

# Защищенные эндпоинты (только для авторизованных пользователей)
current_active_user = fastapi_users.current_user(active=True)


@app.on_event("startup")
async def on_startup():
    """
    Создание таблиц в базе данных при запуске приложения.
    """
    await create_db_and_tables()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(deleteExpiredLinks())
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/links/shorten", response_model=LinkResponse, tags=["links"])
async def shorten_link(
    link_data: LinkCreate,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
    # user=Depends(current_active_user),
):
    """
    Создает короткую ссылку.
    """
    link_manager = LinkManager(session)
    expires_at = link_data.expires_at or None
    link = await link_manager.create_link(
        original_url=link_data.original_url,
        custom_alias=link_data.custom_alias,
        # user_id=id,
        expires_at=expires_at,
    )

    if isinstance(link, str):
        raise HTTPException(status_code=400, detail=link)
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        custom_alias=link.custom_alias,
        created_at=link.created_at,
        expires_at=link.expires_at,
        access_count=link.access_count,
    )


@app.get("/links/search", response_model=LinkSearch, tags=["links"])
async def get_link_stats(
    original_url: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
):
    link_manager = LinkManager(session)
    link = await link_manager.get_link_by_original_url(original_url)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return LinkSearch(
        original_url=link.original_url,
        short_code=link.short_code,
        custom_alias=link.custom_alias,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


@app.get("/links/{short_code}", tags=["links"])
async def redirect_to_original_url(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
):
    """
    Перенаправляет на оригинальный URL по короткому коду.
    """
    link_manager = LinkManager(session)
    link = await link_manager.get_link_and_visit_by_short_code(short_code)
    print(f"orig url = {link.original_url} ; short_code = {link.short_code}")
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Срок действия ссылки истек")
    link.increment_access_count()
    await session.commit()
    return RedirectResponse(url=link.original_url)


@app.get("/links/{short_code}/stats", response_model=LinkStatsResponse, tags=["links"])
async def get_link_stats(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
):
    """
    Возвращает статистику по ссылке.
    """
    link_manager = LinkManager(session)
    link = await link_manager.get_link_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return LinkStatsResponse(
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        access_count=link.access_count,
        last_accessed_at=link.last_accessed_at,
    )



@app.delete("/links/delete_by_short_code/{short_code}", tags=["links"])
async def delete_link_by_short_code(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
    # user=Depends(current_active_user),
):
    """
    Удаляет ссылку по короткому коду.
    """
    link_manager = LinkManager(session)
    success = await link_manager.delete_link_by_short_code(short_code)
    if not success:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return {"message": "Ссылка успешно удалена"}

@app.delete("/links/delete_by_custom_alias/{custom_alias}", tags=["links"])
async def delete_link_by_custom_alias(
    custom_alias: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
    # user=Depends(current_active_user),
):
    """
    Удаляет ссылку по кастомной аббревиатуре.
    """
    link_manager = LinkManager(session)
    success = await link_manager.delete_link_by_custom_alias(custom_alias)
    if not success:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return {"message": "Ссылка успешно удалена"}


@app.put("/links/{short_code}", response_model=LinkResponse, tags=["links"])
async def update_link(
    short_code: str,
    new_url: str,
    session: AsyncSession = Depends(get_async_session),  # Используем Depends для получения сессии
):
    """
    Обновляет оригинальный URL для короткой ссылки.
    """
    link_manager = LinkManager(session)
    link = await link_manager.update_link(short_code, new_url)
    if link is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        custom_alias=link.custom_alias,
        created_at=link.created_at,
        expires_at=link.expires_at,
        access_count=link.access_count,
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", log_level="info")