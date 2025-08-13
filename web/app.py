# web/app.py
from flask import Flask, render_template, request, session
from config.settings import settings
from infrastructure.database import init_db, Session
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
from infrastructure.database.models import Book, Chapter, PlotLine, PlotEvent
from cli.generate_chapters import main as generate_chapters_cli
from sqlalchemy import delete
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализируем БД
Session = init_db(settings.DB_URL)

# Временный user_id
USER_ID = 1
BOOK_ID = 1  # 🔥 Работаем ТОЛЬКО с первой книгой


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-outline", methods=["POST"])
def generate_outline():
    description = request.form["description"]
    title = request.form.get("title", "Новая книга")

    logger.info(f"[WEB] Генерация сюжета: {description}")
    session = Session()

    try:
        # Инициализируем компоненты
        llm = LLMClientFactory.create_client(language='gemini')  # Убедись, что gemini поддерживает русский
        generator = BookGenerator(llm)
        manager = OutlineManager(session)

        # 🔽 УДАЛЯЕМ старую книгу (id=1) и всё, что с ней связано
        session.execute(delete(PlotEvent).where(PlotEvent.chapter.has(book_id=BOOK_ID)))
        session.execute(delete(PlotLine).where(PlotLine.book_id == BOOK_ID))
        session.execute(delete(Chapter).where(Chapter.book_id == BOOK_ID))
        session.execute(delete(Book).where(Book.id == BOOK_ID))
        session.commit()

        # Генерируем сюжет
        storylines, chapters = generator.generate_outline(description)

        # 🔽 СОЗДАЁМ новую книгу с id=1
        # manager.save_outline теперь сохранит всё с book_id=1
        manager.save_outline(
            book_title=title,
            premise=description,
            storylines=storylines,
            chapters=chapters,
            user_id=USER_ID
        )

        # 🔽 Загружаем только book_id=1
        data = manager.load_outline(book_id=BOOK_ID)
        if not data:
            return "<div class='alert alert-danger'>Не удалось загрузить сюжет</div>", 500

        storylines = data["storylines"]
        chapters = data["chapters"]

        # Возвращаем HTML-таблицу
        return render_template("partials/outline_table.html",
                             storylines=storylines,
                             chapters=chapters)

    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        session.rollback()
        return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500

    finally:
        session.close()

@app.route("/generate-chapters", methods=["POST"])
def generate_chapters():
    try:
        # Вызываем существующий CLI-код, но в вебе
        generate_chapters_cli(language="Русский", book_id=1, user_id=USER_ID)
        return "<div class='alert alert-success mt-3'>✅ Главы сгенерированы и сохранены в базу!</div>"
    except Exception as e:
        logger.error(f"Ошибка при генерации глав: {e}")
        return f"<div class='alert alert-danger mt-3'>❌ Ошибка: {str(e)}</div>"


@app.route("/toggle-chapter", methods=["POST"])
def toggle_chapter():
    user_id = get_current_user_id()
    book_id = int(request.form["book_id"])
    chapter_num = int(request.form["chapter_num"])
    enabled = request.form.get("enabled") == "true"

    # Проверяем, что книга принадлежит пользователю
    session = Session()
    try:
        book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if not book:
            return "Access denied", 403

        manager = OutlineManager(session)
        manager.toggle_chapter_generate(book_id, chapter_num, enabled)

        # Возвращаем обновлённый чекбокс
        checked_attr = "checked" if enabled else ""
        return f'<input type="checkbox" hx-post="/toggle-chapter" hx-include="[name=book_id]" hx-vals=\'{{"chapter_num":{chapter_num}, "enabled":{str(not enabled).lower()}}}\' hx-swap="outerHTML" {checked_attr}>'
    finally:
        session.close()


def get_current_user_id():
    # Пока возвращаем 1, потом будет из сессии
    return session.get("user_id", 1)  # fallback на 1

@app.route("/books")
def my_books():
    user_id = get_current_user_id()  # пока 1
    session = Session()
    try:
        books = session.query(Book).filter(Book.user_id == user_id).all()
        return render_template("books.html", books=books)
    finally:
        session.close()


@app.route("/book/<int:book_id>")
def view_book(book_id):
    user_id = get_current_user_id()
    session = Session()
    try:
        book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if not book:
            return "<div class='alert alert-danger'>Книга не найдена</div>", 404

        manager = OutlineManager(session)
        data = manager.load_outline(book_id)
        if not data:
            return "<div class='alert alert-warning'>Сюжет не сгенерирован</div>"

        return render_template("book_outline.html",
                             book=book,
                             storylines=data["storylines"],
                             chapters=data["chapters"])
    finally:
        session.close()

@app.route("/chapter/<int:book_id>/<int:chapter_num>")
def view_chapter(book_id, chapter_num):
    user_id = get_current_user_id()
    session = Session()
    try:
        # Проверяем, что книга принадлежит пользователю
        book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if not book:
            return "<div class='alert alert-danger'>Доступ запрещён</div>", 403

        # Находим главу
        chapter = session.query(Chapter).filter(
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
        session.close()
    
if __name__ == "__main__":
    app.run(debug=True)