# infrastructure/database/__init__.py
"""
Инициализация базы данных и экспорт сессии.
"""
from .models import init_db as _init_db, engine as _engine, Base
from sqlalchemy.orm import sessionmaker

# Глобальный Session — будет инициализирован после вызова init_db
Session = None

def init_db(db_url="sqlite:///storywriter.db"):
    global Session
    engine = _init_db(db_url)  # вызываем оригинальную функцию из models
    Session = sessionmaker(bind=engine)
    return Session

# Опционально: можно сразу создать сессию после init_db, но лучше — по требованию