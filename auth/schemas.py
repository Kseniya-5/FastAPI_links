from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel, Field
from datetime import datetime

class UserRead(schemas.BaseUser[UUID]):
    """
    Схема для чтения информации о пользователе.
    """
    username: str  # Уникальное имя пользователя
    email: str  # Уникальный email


class UserCreate(schemas.BaseUserCreate):
    """
    Схема для создания нового пользователя.
    """
    username: str = Field(..., min_length=3, max_length=100)  # Уникальное имя пользователя
    email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )  # Валидация email через pattern
    password: str = Field(..., min_length=8)  # Пароль (минимум 8 символов)


class UserUpdate(schemas.BaseUserUpdate):
    """
    Схема для обновления информации о пользователе.
    """
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[str] = Field(
        None,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    password: Optional[str] = Field(None, min_length=8)


class LinkCreate(BaseModel):
    """
    Схема для создания новой ссылки.
    """
    original_url: str = Field(..., description="Оригинальный URL")
    custom_alias: Optional[str] = Field(None, description="Кастомный alias")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия")


class LinkResponse(BaseModel):
    """
    Схема для ответа при создании или получении ссылки.
    """
    short_code: str = Field(..., description="Короткий код ссылки")
    original_url: str = Field(..., description="Оригинальный URL")
    custom_alias: Optional[str] = Field(None, description="Кастомный alias")
    created_at: datetime = Field(..., description="Дата создания")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия")
    access_count: int = Field(0, description="Количество переходов")


class LinkStatsResponse(BaseModel):
    """
    Схема для статистики по ссылке.
    """
    original_url: str = Field(..., description="Оригинальный URL")
    created_at: datetime = Field(..., description="Дата создания")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия")
    access_count: int = Field(0, description="Количество переходов")
    last_accessed_at: Optional[datetime] = Field(None, description="Дата последнего использования")

class LinkSearch(BaseModel):
    """
    Схема для ответа на поиск ссылки по url
    """
    short_code: str = Field(..., description="Короткий код ссылки")
    custom_alias: Optional[str] = Field(None, description="Кастомный alias")
    original_url: str = Field(..., description="Оригинальный URL")
    created_at: datetime = Field(..., description="Дата создания")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия")