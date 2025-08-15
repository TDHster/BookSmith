# infrastructure/database/setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User
from config.settings import settings
from werkzeug.security import generate_password_hash
from logger import logger

# Глобальные переменные
engine = None
Session = None


def init_db(db_url: str = settings.DATABASE_URL):
    global engine, Session

    logger.debug("🔧 1. Запуск init_db")
    engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
    logger.debug("✅ 2. Движок создан")

    Session = sessionmaker(bind=engine)
    logger.debug("✅ 3. Session фабрика создана")

    Base.metadata.create_all(engine)
    logger.debug("✅ 4. Таблицы созданы")

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
            print("✅ 5. Пользователи добавлены")
        else:
            print("ℹ️ 5. Пользователи уже есть")
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователей: {e}")
        session.rollback()
        raise  # 🔥 Покажем ошибку
    finally:
        session.close()

    print("✅ 6. init_db завершён, возвращаем Session")
    return Session  # ✅ Обязательно

