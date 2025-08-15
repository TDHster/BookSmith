# infrastructure/database/setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User
from config.settings import settings
from werkzeug.security import generate_password_hash

# Глобальные переменные
engine = None
Session = None


def init_db(db_url: str = settings.DB_PATH):
    """
    Инициализирует движок, создаёт таблицы, добавляет тестовых пользователей.
    Возвращает фабрику сессий.
    """
    global engine, Session

    # Создаём движок
    engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)

    # Создаём таблицы
    Base.metadata.create_all(engine)

    # Добавляем тестовых пользователей, если их нет
    session = Session()
    try:
        if session.query(User).first() is None:
            users = [
                User(
                    username="admin",
                    email="admin@example.com",
                    password=generate_password_hash("admin12344494949494")
                ),
                User(
                    username="writer",
                    email="writer@example.com",
                    password=generate_password_hash("writer1449494848474723")
                ),
            ]
            session.add_all(users)
            session.commit()
            print("✅ Созданы тестовые пользователи: admin, writer")
        else:
            print("ℹ️ Пользователи уже существуют")
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователей: {e}")
        session.rollback()
    finally:
        session.close()

    return Session