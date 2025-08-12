# web/app.py
from flask import Flask, render_template, request, jsonify
from config.settings import settings
from infrastructure.database import init_db, Session
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализируем БД
Session = init_db(settings.DB_URL)

# Временный user_id
USER_ID = 1

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate-outline", methods=["POST"])
def generate_outline():
    description = request.form["description"]
    title = request.form.get("title", "Новая книга")
    
    logger.info(f"[WEB] Генерация сюжета: {description}")

    # Инициализируем компоненты
    session = Session()
    llm = LLMClientFactory.create_client(language='Русский')
    generator = BookGenerator(llm)
    manager = OutlineManager(session)

    try:
        # Генерируем сюжет
        storylines, chapters = generator.generate_outline(description)

        # Сохраняем в БД
        manager.save_outline(
            book_title=title,
            premise=description,
            storylines=storylines,
            chapters=chapters,
            user_id=USER_ID
        )

        # Загружаем обратно (чтобы отдать в шаблон)
        data = manager.load_outline(book_id=1)  # временно: первая книга
        storylines = data["storylines"]
        chapters = data["chapters"]

        # Возвращаем HTML-таблицу
        return render_template("partials/outline_table.html",
                             storylines=storylines,
                             chapters=chapters)
    
    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        return f"<div class='alert alert-danger'>Ошибка: {str(e)}</div>", 500

if __name__ == "__main__":
    app.run(debug=True)