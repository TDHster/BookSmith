import argparse
from pathlib import Path
import pandas as pd
from config.settings import settings
from infrastructure.llm_client import GeminiClient
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator

def setup_directories():
    Path(settings.CHAPTERS_DIR).mkdir(exist_ok=True)

def main():
    setup_directories()
    llm = GeminiClient()
    generator = BookGenerator(llm)
    manager = OutlineManager()
    
    # Загружаем структуру книги
    df = manager.load_outline()
    storylines = [col for col in df.columns if col not in ["Chapter", "Title", "Generate", "Summary", "File"]]
    
    print("Generating chapters...")
    
    # Сортируем главы по номеру
    df = df.sort_values(by="Chapter")
    
    for index, row in df.iterrows():
        if row["Generate"] != "✅":
            continue
        
        chapter_num = int(row["Chapter"])
        
        # 1. Перед каждой генерацией заново читаем весь Excel
        current_df = manager.load_outline()
        
        # 2. Собираем саммари всех предыдущих глав
        previous_summaries = []
        for _, prev_row in current_df.iterrows():
            prev_chapter_num = int(prev_row["Chapter"])
            if prev_chapter_num < chapter_num and prev_row["Summary"] and not pd.isna(prev_row["Summary"]):
                previous_summaries.append(f"Chapter {prev_chapter_num}: {prev_row['Summary']}")
        
        # 3. Подготавливаем данные главы
        chapter_data = {
            "chapter": chapter_num,
            "title": row["Title"],
            "events": {sl: row[sl] for sl in storylines}
        }
        
        # 4. Генерируем главу
        print(f"Generating chapter {chapter_num}...")
        chapter_text, summary = generator.generate_chapter(
            chapter_data,
            "Generated from outline",
            storylines,
            previous_summaries
        )
        
        # 5. Сохраняем главу в файл
        filename = f"{settings.CHAPTERS_DIR}/chapter_{chapter_num}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(chapter_text)
        
        # 6. Обновляем Excel (снимаем галочку и добавляем саммари)
        manager.update_outline(chapter_num, summary, filename)
        print(f"Chapter {chapter_num} generated. Summary: {summary[:50]}...")
    
    print("All chapters generated!")

if __name__ == "__main__":
    main()