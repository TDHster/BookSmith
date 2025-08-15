# web/routes/outline_routes.py
from flask import request, session, render_template
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from infrastructure.database import get_session
from infrastructure.database.models import Book, Chapter, PlotEvent, PlotLine
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
from logger import logger

def init_outline_routes(app):
    @app.route("/update-event", methods=["POST"])
    def update_event():
        try:
            user_id = session.get("user_id")
            book_id = int(request.form["book_id"])
            chapter_num = int(request.form["chapter_num"])
            storyline_name = request.form["storyline"]
            new_text = request.form["text"]

            session_db = get_session()
            try:
                book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
                if not book:
                    return "Access denied", 403

                manager = OutlineManager(session_db)
                manager.update_plot_event(book_id, chapter_num, storyline_name, new_text)

                return f'''
                <textarea 
                  name="text"  
                  class="form-control form-control-sm"
                  hx-post="/update-event"
                  hx-include="[name=book_id]"
                  hx-vals='{{"chapter_num": {chapter_num}, "storyline": "{storyline_name}"}}'
                  hx-trigger="blur"
                  hx-target="this"
                  hx-swap="outerHTML"
                  rows="6"
                  style="font-size: 0.9rem; padding: 4px;"
                >{new_text}</textarea>
                '''
            finally:
                session_db.close()

        except Exception as e:
            logger.error(f"Ошибка при обновлении события: {e}")
            return f"<div class='text-danger'>Ошибка: {str(e)}</div>", 500

    @app.route("/regenerate-outline", methods=["POST"])
    def regenerate_outline():
        try:
            user_id = session.get("user_id")

            if 'book_id' not in request.form or 'premise' not in request.form:
                return "<div class='alert alert-danger'>Недостающие данные</div>", 400

            book_id = int(request.form["book_id"])
            new_premise = request.form["premise"].strip()

            session_db = get_session()
            try:
                book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
                if not book:
                    return "<div class='alert alert-danger'>Доступ запрещён</div>", 403

                # ✅ Удаляем ТОЛЬКО сюжет и главы, НО НЕ книгу
                session_db.execute(delete(PlotEvent).where(PlotEvent.chapter.has(book_id=book_id)))
                session_db.execute(delete(PlotLine).where(PlotLine.book_id == book_id))
                session_db.execute(delete(Chapter).where(Chapter.book_id == book_id))
                session_db.commit()

                # Теперь перезаписываем сюжет
                llm = LLMClientFactory.create_client(language='gemini')
                generator = BookGenerator(llm)
                storylines, chapters = generator.generate_outline(new_premise)

                manager = OutlineManager(session_db)
                manager.save_outline(
                    book_title=book.title,
                    premise=new_premise,
                    storylines=storylines,
                    chapters=chapters,
                    user_id=user_id,
                    book_id=book.id  # ✅ Передаём book_id
                )

                # ✅ Теперь load_outline с тем же book_id
                data = manager.load_outline(book_id)
                if not data:
                    return "<div class='alert alert-danger'>Не удалось загрузить сюжет</div>", 500

                return render_template("book_outline_table.html",
                                    book=book,
                                    storylines=data["storylines"],
                                    chapters=data["chapters"])

            finally:
                session_db.close()

        except Exception as e:
            logger.error(f"Ошибка при перегенерации сюжета: {e}")
            return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500