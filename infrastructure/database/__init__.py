# infrastructure/database/__init__.py
"""
Инициализация базы данных и экспорт сессии.
"""
from .setup import init_db, Session, engine

# Теперь можно: from infrastructure.database import init_db, Session