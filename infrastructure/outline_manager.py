# infrastructure/outline_manager.py
from sqlalchemy.orm import Session as DBSession
from infrastructure.database.models import Book, Chapter, PlotLine, PlotEvent
from typing import List, Dict

class OutlineManager:
    def __init__(self, db_session: DBSession):
        self.session = db_session

    def save_outline(
        self,
        book_title: str,
        premise: str,
        storylines: list,
        chapters: list,
        user_id: int = 1
    ):
        """
        Сохраняет книгу, сюжетные линии и события глав в БД.
        """
        # Создаём книгу
        book = Book(
            title=book_title,
            premise=premise,
            user_id=user_id
        )
        self.session.add(book)
        self.session.flush()  # Получаем book.id

        # Создаём сюжетные линии
        line_objects = []
        for name in storylines:
            line = PlotLine(name=name, book_id=book.id)
            self.session.add(line)
            line_objects.append(line)
        self.session.flush()

        # Маппинг: имя линии → объект
        line_map = {line.name: line for line in line_objects}

        # Главы и события
        for ch in chapters:
            chapter = Chapter(
                book_id=book.id,
                number=ch["chapter"],
                title=ch.get("title", f"Глава {ch['chapter']}"),
                generate_flag=True
            )
            self.session.add(chapter)
            self.session.flush()

            # События по линиям
            for storyline_name, event_desc in ch["events"].items():
                if storyline_name in line_map and event_desc.strip():
                    event = PlotEvent(
                        chapter_id=chapter.id,
                        plot_line_id=line_map[storyline_name].id,
                        description=str(event_desc)
                    )
                    self.session.add(event)

        self.session.commit()
        print(f"✅ Книга '{book.title}' и сюжет сохранены в БД")

    def load_outline(self, book_id: int):
        """
        Загружает книгу и сюжет в формате, похожем на Excel.
        """
        book = self.session.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None

        chapters = (
            self.session.query(Chapter)
            .filter(Chapter.book_id == book_id)
            .order_by(Chapter.number)
            .all()
        )

        lines = (
            self.session.query(PlotLine)
            .filter(PlotLine.book_id == book_id)
            .all()
        )
        line_names = [line.name for line in lines]
        line_map = {line.id: line.name for line in lines}

        events = (
            self.session.query(PlotEvent)
            .join(PlotLine)
            .filter(PlotLine.book_id == book_id)
            .all()
        )

        event_map = {}
        for ev in events:
            ch_id = ev.chapter_id
            if ch_id not in event_map:
                event_map[ch_id] = {}
            event_map[ch_id][line_map[ev.plot_line_id]] = ev.description

        data = []
        for ch in chapters:
            row = {
                "Chapter": ch.number,
                "Title": ch.title,
                "Generate": "✅" if ch.generate_flag else "",
                "Summary": ch.content or "",
                "File": ch.context_summary or ""
            }
            for line_name in line_names:
                row[line_name] = event_map.get(ch.id, {}).get(line_name, "")
            data.append(row)

        return {
            "book": {"title": book.title, "premise": book.premise},
            "storylines": line_names,
            "chapters": data
        }
        
    def update_chapter_summary(self, book_id: int, chapter_number: int, summary: str, content: str = None):
        """
        Обновляет главу: снимает флаг generate, добавляет summary и (опционально) текст.
        """
        chapter = (
            self.session.query(Chapter)
            .join(Book)
            .filter(Book.id == book_id, Chapter.number == chapter_number)
            .first()
        )
        if not chapter:
            raise ValueError(f"Глава {chapter_number} в книге {book_id} не найдена")

        chapter.generate_flag = False
        chapter.context_summary = summary
        if content:
            chapter.content = content
        self.session.commit()
            