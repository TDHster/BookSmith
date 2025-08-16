# web/routes/chapter_routes.py
from flask import request, session, render_template
from sqlalchemy.orm import sessionmaker

from infrastructure.database import get_session
from infrastructure.database.models import Book, Chapter  
from infrastructure.outline_manager import OutlineManager
# from cli.generate_chapters import main as generate_chapters_cli
from cli.generate_chapters import generate_chapters_for_book  

from logger import logger

def init_chapter_routes(app):
    @app.route("/generate-chapters", methods=["POST"])
    def generate_chapters():
        try:
            user_id = session.get("user_id")
            book_id = int(request.form["book_id"])
            logger.info(f"Запуск генерации глав для {book_id=} (user_id={user_id})")

            # ✅ Вызываем чистую функцию
            success = generate_chapters_for_book(book_id=book_id, user_id=user_id)

            if not success:
                return "<div class='alert alert-danger'>Не удалось сгенерировать главы</div>"

            # Перезагружаем данные
            session_db = get_session()
            try:
                book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
                if not book:
                    return "<div class='alert alert-danger'>Книга не найдена</div>", 404

                manager = OutlineManager(session_db)
                data = manager.load_outline(book_id)
                if not data:
                    return "<div class='alert alert-warning'>Сюжет не сгенерирован</div>"

                return render_template("book_outline_table.html",
                                     book=book,
                                     storylines=data["storylines"],
                                     chapters=data["chapters"])
            finally:
                session_db.close()

        except Exception as e:
            logger.error(f"Ошибка при генерации глав: {e}")
            return f"<div class='alert alert-danger mt-3'>❌ Ошибка: {str(e)}</div>"
        
    @app.route("/toggle-chapter", methods=["POST"])
    def toggle_chapter():
        user_id = session.get("user_id")
        book_id = int(request.form["book_id"])
        chapter_num = int(request.form["chapter_num"])
        enabled = request.form.get("enabled") == "true"

        session_db = get_session()
        try:
            book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
            if not book:
                return "Access denied", 403

            manager = OutlineManager(session_db)
            manager.toggle_chapter_generate(book_id, chapter_num, enabled)

            checked_attr = "checked" if enabled else ""
            return f'<input type="checkbox" hx-post="/toggle-chapter" hx-include="[name=book_id]" hx-vals=\'{{"chapter_num":{chapter_num}, "enabled":{str(not enabled).lower()}}}\' hx-swap="outerHTML" {checked_attr}>'
        finally:
            session_db.close()

    @app.route("/chapter/<int:book_id>/<int:chapter_num>")
    def view_chapter(book_id, chapter_num):
        user_id = session.get("user_id")
        session_db = get_session()
        try:
            book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
            if not book:
                return "<div class='alert alert-danger'>Доступ запрещён</div>", 403

            chapter = session_db.query(Chapter).filter(
                Chapter.book_id == book_id,
                Chapter.number == chapter_num
            ).first()

            if not chapter or not chapter.content:
                return "<div class='alert alert-warning'>Глава не найдена или ещё не сгенерирована.</div>", 404

            return render_template("chapter.html", book=book, chapter=chapter)
        except Exception as e:
            logger.error(f"Ошибка при загрузке главы {chapter_num}: {e}")
            return "<div class='alert alert-danger'>Ошибка при загрузке главы.</div>", 500
        finally:
            session_db.close()