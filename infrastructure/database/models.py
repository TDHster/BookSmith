# infrastructure/database/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    premise = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="books")
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    plot_lines = relationship("PlotLine", back_populates="book", cascade="all, delete-orphan")


class PlotLine(Base):
    __tablename__ = 'plot_lines'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'))

    book = relationship("Book", back_populates="plot_lines")
    events = relationship("PlotEvent", back_populates="plot_line", cascade="all, delete-orphan")


class PlotEvent(Base):
    __tablename__ = 'plot_events'
    id = Column(Integer, primary_key=True)
    plot_line_id = Column(Integer, ForeignKey('plot_lines.id'))
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    description = Column(Text, nullable=False)

    plot_line = relationship("PlotLine", back_populates="events")
    chapter = relationship("Chapter", back_populates="plot_events")


class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'))
    number = Column(Integer, nullable=False)
    title = Column(String(200))
    generate_flag = Column(Boolean, default=False)
    content = Column(Text)
    context_summary = Column(Text)
    generated_at = Column(DateTime, nullable=True)

    book = relationship("Book", back_populates="chapters")
    plot_events = relationship("PlotEvent", back_populates="chapter")


# Глобальные переменные
engine = None
Session = None


def setup_database(db_url: str = settings.DB_PATH):
    """
    Инициализирует базу данных: создаёт таблицы и добавляет тестовых пользователей.
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
        from sqlalchemy import select
        if session.query(User).first() is None:
            users = [
                User(
                    username="admin",
                    email="admin@example.com",
                    password="admin12344494949494"  # В продакшене — хэшировать!
                ),
                User(
                    username="writer",
                    email="writer@example.com",
                    password="writer1449494848474723"
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