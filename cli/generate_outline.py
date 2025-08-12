# cli/generate_outline.py
import argparse
from infrastructure.llm_client import LLMClientFactory
from infrastructure.database import init_db, Session
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from config.settings import settings
from logger import logger

def main(description: str, language: str, title: str = "Новая книга"):
    # Инициализируем БД
    Session = init_db(settings.DB_URL)
    session = Session()

    # Генерируем сюжет
    llm = LLMClientFactory.create_client(language)
    generator = BookGenerator(llm)
    logger.info(f"Generating book outline: {description}")

    storylines, chapters = generator.generate_outline(description)

    # Сохраняем в БД
    manager = OutlineManager(session)
    manager.save_outline(
        book_title=title,
        premise=description,
        storylines=storylines,
        chapters=chapters,
        user_id=1  # временно
    )

    logger.info(f"✅ Сюжет сохранён в БД: книга '{title}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сгенерировать сюжет книги")
    parser.add_argument("--description", required=True, help="Описание книги")
    parser.add_argument("--title", default="Моя книга", help="Название книги")
    parser.add_argument("--language", default="gemini", help="Язык LLM")
    args = parser.parse_args()

    main(args.description, args.language, args.title)