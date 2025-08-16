# cli/generate_chapters.py
from config.settings import settings
from infrastructure.database.models import Book
from infrastructure.database import init_db, get_session
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from infrastructure.llm_client import LLMClientFactory
from logger import logger
import argparse


def generate_chapters_for_book(book_id: int, user_id: int, language: str = settings.DEFAULT_LANGUAGE):
    """
    Основная логика генерации глав — для вызова из веб-слоя.
    НЕ использует argparse, не вызывает init_db напрямую.
    """
    session = get_session()

    try:
        # Проверяем, что книга существует и принадлежит пользователю
        book = session.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if not book:
            logger.error(f"Книга {book_id} не найдена или доступ запрещён для {user_id=}")
            return False

        llm = LLMClientFactory.create_client(language)
        generator = BookGenerator(llm)
        manager = OutlineManager(session)

        logger.debug(f"Запуск генерации глав для книги '{book.title}' {book_id=}")

        # Загружаем структуру книги
        data = manager.load_outline(book_id)
        if not data:
            logger.error(f"Не удалось загрузить сюжет для книги {book_id}")
            return False

        storylines = data["storylines"]
        chapters = sorted(data["chapters"], key=lambda x: x["Chapter"])

        # Генерируем главы
        for row in chapters:
            if row.get("Generate") != True:
                continue

            chapter_num = int(row["Chapter"])
            logger.info(f"Generating chapter {chapter_num}...")

            # Собираем контекст предыдущих глав
            previous_summaries = []
            for ch in chapters:
                prev_num = int(ch["Chapter"])
                if prev_num < chapter_num and ch.get("Summary"):
                    previous_summaries.append(f"Глава {prev_num}: {ch['Summary']}")

            # Подготовка данных
            chapter_data = {
                "chapter": chapter_num,
                "title": row["Title"],
                "events": {sl: row[sl] for sl in storylines if sl in row}
            }

            # Генерация
            chapter_text, summary = generator.generate_chapter(
                chapter_data=chapter_data,
                book_description=book.premise,
                storylines=storylines,
                previous_summaries=previous_summaries,
                chapter_length=settings.CHAPTER_LENGTH  # ✅ Исправил опечатку: LENGHT → LENGTH
            )

            # Сохранение напрямую в БД
            manager.update_chapter_summary(
                book_id=book_id,
                chapter_number=chapter_num,
                summary=summary,
                content=chapter_text
            )

            logger.debug(f"✅ Глава {chapter_num} сохранена в БД. Summary: {summary[:60]}...")

        logger.info(f"Генерация для '{book.title}' завершена.")
        return True

    except Exception as e:
        logger.error(f"Ошибка при генерации глав: {e}")
        return False

    finally:
        session.close()  # ✅ Обязательно закрываем сессию


def main(book_id: int, user_id: int, language: str = settings.DEFAULT_LANGUAGE):
    """
    CLI-интерфейс. Инициализирует БД и вызывает основную логику.
    """
    # Инициализируем БД (нужно только в CLI)
    init_db(settings.DATABASE_URL)

    # Вызываем основную логику
    success = generate_chapters_for_book(book_id=book_id, user_id=user_id, language=language)
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сгенерировать главы книги")
    parser.add_argument("--book-id", type=int, required=True, help="ID книги")
    parser.add_argument("--user-id", type=int, default=1, help="ID пользователя")
    parser.add_argument("--language", default="gemini", help="LLM: gemini, openai и т.д.")
    args = parser.parse_args()

    main(book_id=args.book_id, user_id=args.user_id, language=args.language)