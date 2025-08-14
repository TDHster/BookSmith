# infrastructure/database/__init__.py
"""
Инициализация базы данных и экспорт сессии.
"""
from .models import setup_database, Session

# Просто экспонируем функцию инициализации
# Теперь в web/app.py можно: from infrastructure.database import init_db, Session
init_db = setup_database