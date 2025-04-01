from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# from auth.database import engine

Base = declarative_base()

class User(Base):
    """
    Модель, которая хранит информацию о зарегистрированных пользователях.
    Также поле 'links' определяет связь 'один ко многим' с моделью Link,
    что позволяет каждому пользователю владеть несколькими ссылками.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)        # Хэшированный пароль
    created_at = Column(DateTime, default=datetime.utcnow)       # Дата создания пользователя
    is_active = Column(Boolean, default=True)                    # Флаг активности пользователя
    links = relationship('Link', back_populates='user')

    # id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # Уникальное имя пользователя
    # email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # Уникальный email
    # created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Дата создания пользователя
    # is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Флаг активности пользователя
    # is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)  # Флаг суперпользователя
    # is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # Флаг верификации пользователя


class Link(Base):
    """
    Модель ссылки, которая хранит информацию о коротких ссылках и их оригинальных URL.
    Также поле 'user' определяет связь 'многие к одному'.
    """
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(50), unique=True, nullable=False)
    custom_alias = Column(String(50), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)       # Дата создания ссылки
    expires_at = Column(DateTime, nullable=True)                 # Дата окончания действия ссылки
    last_accessed_at = Column(DateTime, nullable=True)           # Дата последнего использования
    access_count = Column(Integer, default=0)                    # Количество переходов по ссылке

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship('User', back_populates='links')

    def increment_access_count(self):
        """
        Увеличивает счетчик переходов и обновляет дату последнего доступа.
        """
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()


class LinkStats(Base):
    """
    Модель статистики ссылок, которая хранит историю доступа к ссылкам.
    Эта модель позволяет отслеживать детальную статистику по каждому переходу
    """
    __tablename__ = 'link_stats'

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey('links.id'), nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow)            # Дата и время доступа
    ip_address = Column(String(50), nullable=True)                     # IP-адрес пользователя
    user_agent = Column(Text, nullable=True)                           # User-Agent браузера

    link = relationship('Link', backref='stats')
