# web/app.py
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from config.settings import settings
from infrastructure.database import init_db, Session
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
from infrastructure.database.models import Book, Chapter, PlotLine, PlotEvent, User
from cli.generate_chapters import main as generate_chapters_cli
from sqlalchemy import delete
from time import sleep
from collections import defaultdict
import logging
from logger import logger

app = Flask(__name__)

# Инициализируем БД
Session = init_db(settings.DB_URL)

failed_attempts = defaultdict(int)

@app.route("/")
def index():
    # return render_template("index.html")
    return redirect("/books")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 🔒 Увеличиваем счётчик попыток для IP или username
        # Можно использовать: request.remote_addr (IP) или username
        # ip = request.remote_addr  # или username, если хочешь по пользователю
        ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]
        failed_attempts[ip] += 1
        attempts = failed_attempts[ip]

        # ⏳ Экспоненциальная задержка: 1, 2, 4, 8... секунд
        if attempts > 1:
            delay = 2 ** (attempts - 2)  # 1, 2, 4, 8...
            delay = min(delay, 30)      # максимум 30 сек
            sleep(delay)

        session_db = Session()
        try:
            user = session_db.query(User).filter(User.username == username).first()
            # if user and user.password == password:
            if user and check_password_hash(user.password, password):
                # ✅ Успех — сбрасываем счётчик
                failed_attempts[ip] = 0
                session["user_id"] = user.id
                logger.info(f'User {user} logged in from ip {ip}')
                return redirect("/books")
            else:
                logger.error(f'User {user} failed logged in from ip {ip} attempt {attempts}')
                # ❌ Ошибка — оставляем счётчик
                return "<div class='alert alert-danger'>Неверный логин или пароль</div>", 401
        finally:
            session_db.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")


@app.route("/new-book")
def new_book_form():
    return render_template("new_book.html")

@app.route("/create-book", methods=["POST"])
def create_book():
    description = request.form["description"]
    title = request.form.get("title", "Новая книга")
    user_id = get_current_user_id()

    logger.info(f"[WEB] Создание новой книги: {title}")
    session = Session()

    try:
        # Инициализируем компоненты
        llm = LLMClientFactory.create_client(language='gemini')
        generator = BookGenerator(llm)
        manager = OutlineManager(session)

        # Генерируем сюжет
        storylines, chapters = generator.generate_outline(description)

        # Сохраняем как НОВУЮ книгу
        manager.save_outline(
            book_title=title,
            premise=description,
            storylines=storylines,
            chapters=chapters,
            user_id=user_id
        )

        # Находим ID новой книги
        book = session.query(Book).filter(Book.user_id == user_id).order_by(Book.id.desc()).first()

        # 🔥 Возвращаем HX-Redirect на страницу редактирования
        response = app.response_class()
        response.headers["HX-Redirect"] = f"/book/{book.id}"
        logger.info(f'Creating book {title} {description}')
        return response

    except Exception as e:
        logger.error(f"Ошибка при создании книги: {e}")
        session.rollback()
        return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500
    finally:
        session.close()

@app.route("/generate-chapters", methods=["POST"])
def generate_chapters():
    try:
        user_id = get_current_user_id()
        # book_id = 1  # временно
        book_id = int(request.form["book_id"])
        logger.info(f"Generating chapters for {book_id=}")
        generate_chapters_cli(book_id=book_id, user_id=user_id) 

        session = Session()
        try:
            # Загружаем книгу и сюжет
            book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
            if not book:
                return "<div class='alert alert-danger'>Книга не найдена</div>", 404

            manager = OutlineManager(session)
            data = manager.load_outline(book_id)
            if not data:
                return "<div class='alert alert-warning'>Сюжет не сгенерирован</div>"

            # Передаём book и chapters
            return render_template("book_outline_table.html",
                                 book=book,  # 🔥 Добавь это!
                                 storylines=data["storylines"],
                                 chapters=data["chapters"])
        finally:
            session.close()

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
    return session.get("user_id")


@app.route("/books")
def my_books():
    user_id = get_current_user_id()
    if not user_id:
        return redirect("/login")
    
    session_db = Session()
    try:
        books = session_db.query(Book).filter(Book.user_id == user_id).all()
        return render_template("books.html", books=books)
    finally:
        session_db.close()


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

@app.route("/delete-book", methods=["POST"])
def delete_book():
    try:
        user_id = get_current_user_id()
        book_id = int(request.form["book_id"])

        session = Session()
        try:
            manager = OutlineManager(session)
            manager.delete_book(book_id, user_id)
            logger.info(f"Book {book_id=} deleted")
            # Перенаправляем на список книг
            return """
            <script>
                alert('Книга удалена');
                window.location.href = '/books';
            </script>
            """
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Ошибка при удалении книги: {e}")
        return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500

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
    
@app.route("/update-event", methods=["POST"])
def update_event():
    try:
        print("Form ", request.form)  # для отладки
        user_id = get_current_user_id()
        book_id = int(request.form["book_id"])
        chapter_num = int(request.form["chapter_num"])
        storyline_name = request.form["storyline"]
        new_text = request.form["text"]

        # Проверяем доступ
        session = Session()
        try:
            book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
            if not book:
                return "Access denied", 403

            manager = OutlineManager(session)
            manager.update_plot_event(book_id, chapter_num, storyline_name, new_text)

            # 🔥 Возвращаем ОБНОВЛЁННЫЙ textarea
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
              style="min-height: 60px; font-size: 0.9rem; padding: 4px;"
            >{new_text}</textarea>
            '''

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Ошибка при обновлении события: {e}")
        return f"<div class='text-danger'>Ошибка: {str(e)}</div>", 500


app.secret_key = settings.WEB_APP_SECRET_KEY
    
if __name__ == "__main__":
    # app.run(debug=True)    
    app.run(debug=True, port=8000)  # или 8000, 8081, 8888 и т.д.