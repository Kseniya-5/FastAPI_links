import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Optional

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL
from models.models import Link, User, Base

import hashlib
import base64


def get_hash_10(input_string: str) -> str:
    # Создаем хэш SHA-256 от строки
    hash_object = hashlib.sha256(input_string.encode())
    # Кодируем хэш в base64
    base64_encoded = base64.urlsafe_b64encode(hash_object.digest()).decode('utf-8')
    # Обрезаем до 10 символов
    return base64_encoded[:10]


# Создание асинхронного движка и сессии
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Зависимость для получения асинхронной сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# Функция для создания таблиц в базе данных
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Зависимость для работы с пользовательской базой данных через FastAPI-Users
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# Класс LinkManager для работы со ссылками
class LinkManager:
    """
    Менеджер для работы со ссылками.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.dbm = DBManager()

    async def create_link(
            self,
            original_url: str,
            user_id: Optional[int] = None,
            custom_alias: Optional[str] = None,
            expires_at: Optional[datetime] = None,
    ) -> Link | str:
        """
        Создает новую короткую ссылку.
        """
        short_code = get_hash_10(original_url)

        # проверка есть ли в базе данных такая ссылка
        exist = await self.dbm.getLinkByCode(short_code)
        if exist:
            return f"url already exist with short code {exist.short_code}"
        if custom_alias:
            exist = await self.dbm.getLinkByAlias(custom_alias)
            if exist:
                return "custom_alias already exist"

        res = Link()
        res.original_url = original_url
        res.short_code = short_code
        res.created_at = datetime.now().replace(tzinfo=None)
        res.expires_at = expires_at.replace(tzinfo=None)
        res.custom_alias = custom_alias
        res.user_id = user_id
        res.access_count = 0
        await self.dbm.saveLink(res)
        return res

    async def get_link_and_visit_by_short_code(self, short_code: str) -> Link:
        await self.dbm.visitLink(short_code)
        res = await self.dbm.getLinkByCode(short_code)
        return res

    async def get_link_by_short_code(self, short_code: str) -> Link:
        res = await self.dbm.getLinkByCode(short_code)
        return res

    async def get_link_by_custom_alias(self, custom_alias: str) -> Link:
        res = await self.dbm.getLinkByAlias(custom_alias)
        return res

    async def get_link_by_original_url(self, url: str) -> Link:
        res = await self.dbm.getLinkByUrl(url)
        return res


    async def delete_link_by_short_code(self, short_code: str) -> bool:
        res = await self.dbm.deleteLinkByCode(short_code)
        return res

    async def delete_link_by_custom_alias(self, custom_alias: str) -> bool:
        res = await self.dbm.deleteLinkByAlias(custom_alias)
        return res

    async def update_link(self, short_code: str, newUrl: str) -> Link:
        res = await self.dbm.updateLink(short_code, newUrl)
        return res

class DBManager:
    # операции со ссылками
    async def saveLink(self, link: Link):
        async with async_session() as sess:
            sess.add(link)
            await sess.flush()
            await sess.commit()

    async def getLinkByCode(self, code: str):
        async with async_session() as session:
            query = select(Link).where(Link.short_code == code)
            result = await session.execute(query)
            await session.commit()
            await session.flush()
            return result.scalars().first()

    async def getLinkByAlias(self, custom_alias: str):
        async with async_session() as session:
            query = select(Link).where(Link.custom_alias == custom_alias)
            result = await session.execute(query)
            await session.commit()
            await session.flush()
            return result.scalars().first()

    async def getLinkByUrl(self, url: str):
        async with async_session() as session:
            query = select(Link).where(Link.original_url == url)
            result = await session.execute(query)
            await session.commit()
            await session.flush()
            return result.scalars().first()

    async def visitLink(self, code: str):
        async with async_session() as session:
            await session.execute(update(Link).where(Link.short_code == code).
                                  values(access_count=(Link.access_count + 1),
                                         last_accessed_at=datetime.now().replace(tzinfo=None)))
            await session.commit()
            await session.flush()
            return True

    async def deleteLinkByCode(self, code: str):
        async with async_session() as session:
            res = await session.execute(delete(Link).where(Link.short_code == code))
            await session.commit()
            return res.rowcount > 0

    async def deleteLinkByAlias(self, custom_alias: str):
        async with async_session() as session:
            res = await session.execute(delete(Link).where(Link.custom_alias == custom_alias))
            await session.commit()
            return res.rowcount > 0

    async def updateLink(self, code: str, newUrl: str):
        async with async_session() as session:
            res = await session.execute(update(Link).where(Link.short_code == code).
                                        values(original_url=newUrl).
                                        returning(Link))
            await session.commit()
            return res.scalar_one_or_none()

    # операции с пользователями
    async def saveUser(self, u: User):
        async with async_session() as sess:
            sess.add(u)
            await sess.flush()
            await sess.commit()

    async def getUser(self, u: User):
        return

async def deleteExpiredLinks():
    while True:
        async with async_session() as session:
            try:
                query = delete(Link).where(Link.expires_at < datetime.utcnow())
                await session.execute(query)
                await session.commit()
                print("[info] Expired links deleted")
            except Exception as e:
                print(f"[error] Error deleting expired links: {e}")
                await session.rollback()

        # раз во столько секунд происходит очистка протухших ссылок
        await asyncio.sleep(100)