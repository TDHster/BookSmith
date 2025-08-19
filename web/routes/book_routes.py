# web/routes/book_routes.py
from flask import make_response, request, session, redirect, render_template
from sqlalchemy.orm import sessionmaker

from infrastructure.database import get_session
from infrastructure.database.models import Book, User
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
from cli.generate_chapters import main as generate_chapters_cli
from logger import logger

def get_current_user_id():
    return session.get("user_id")

def init_book_routes(app):
    @app.route("/")
    def index():
        return redirect("/books")

    @app.route("/books")
    def my_books():
        user_id = get_current_user_id()
        if not user_id:
            return redirect("/login")

        session_db = get_session()
        try:
            books = session_db.query(Book).filter(Book.user_id == user_id).all()
            return render_template("books.html", books=books, user_id=user_id)
        finally:
            session_db.close()

    @app.route("/new-book")
    def new_book_form():
        return render_template("new_book.html")

    @app.route("/create-book", methods=["POST"])
    def create_book():
        description = request.form["description"]
        title = request.form.get("title", "Новая книга")
        user_id = get_current_user_id()

        logger.info(f"[WEB] Создание новой книги: {title}")
        session_db = get_session()

        try:
            llm = LLMClientFactory.create_client(language='gemini')
            generator = BookGenerator(llm)
            manager = OutlineManager(session_db)

            storylines, chapters = generator.generate_outline(description)

            manager.save_outline(
                book_title=title,
                premise=description,
                storylines=storylines,
                chapters=chapters,
                user_id=user_id
            )

            book = session_db.query(Book).filter(Book.user_id == user_id).order_by(Book.id.desc()).first()

            response = app.response_class()
            response = make_response("", 307)   
            response.headers["HX-Redirect"] = f"/book/{book.id}"
            logger.info(f'Creating book {title} {description}')
            return response

        except Exception as e:
            logger.error(f"Ошибка при создании книги: {e}")
            session_db.rollback()
            return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500
        finally:
            session_db.close()
            
    @app.route("/book/<int:book_id>")
    def view_book(book_id):
        user_id = get_current_user_id()
        session_db = get_session()  # ✅
        try:
            book = session_db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
            if not book:
                return "<div class='alert alert-danger'>Книга не найдена</div>", 404

            manager = OutlineManager(session_db)
            data = manager.load_outline(book_id)
            if not data:
                return "<div class='alert alert-warning'>Сюжет не сгенерирован</div>"

            return render_template("book_outline.html",
                                 book=book,
                                 storylines=data["storylines"],
                                 chapters=data["chapters"])
        finally:
            session_db.close()