# web/routes/admin_routes.py
from flask import render_template, session
from infrastructure.database import get_session
from infrastructure.database.models import Book, User
from logger import logger

def init_admin_routes(app):
    @app.route("/admin/books")
    def admin_books():
        user_id = session.get("user_id")
        
        # 🔐 Проверка: только user_id=1
        if user_id != 1:
            logger.warning(f"Доступ к /admin/books запрещён.")
            return "<h1>Доступ запрещён</h1><p>У вас нет прав администратора.</p>", 403

        session_db = get_session()
        try:
            # Загружаем все книги + имена пользователей
            books = (
                session_db.query(Book, User.username)
                .join(User, User.id == Book.user_id)
                .order_by(Book.created_at.desc())
                .all()
            )

            # Формируем список словарей для шаблона
            books_data = []
            for book, username in books:
                books_data.append({
                    "id": book.id,
                    "title": book.title,
                    "premise": book.premise,
                    "username": username,
                    "created_at": book.created_at
                })

            return render_template("admin_books.html", books=books_data)

        except Exception as e:
            logger.error(f"Ошибка при загрузке книг для админа: {e}")
            return "<h1>Ошибка сервера</h1>", 500

        finally:
            session_db.close()