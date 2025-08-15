# web/routes/delete_routes.py
from flask import request, session
from sqlalchemy.orm import sessionmaker

from infrastructure.database import get_session
from infrastructure.outline_manager import OutlineManager
from logger import logger

def init_delete_routes(app):
    @app.route("/delete-book", methods=["POST"])
    def delete_book():
        try:
            user_id = session.get("user_id")
            book_id = int(request.form["book_id"])

            session_db = get_session()
            try:
                manager = OutlineManager(session_db)
                manager.delete_book(book_id, user_id)
                logger.info(f"Book {book_id=} deleted")

                return """
                <script>
                    alert('Книга удалена');
                    window.location.href = '/books';
                </script>
                """
            finally:
                session_db.close()

        except Exception as e:
            logger.error(f"Ошибка при удалении книги: {e}")
            return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500