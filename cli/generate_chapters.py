import argparse
from pathlib import Path
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
    
    df = manager.load_outline()
    storylines = [col for col in df.columns if col not in ["Chapter", "Title", "Generate", "Summary", "File"]]
    
    print("Generating chapters...")
    previous_summaries = []
    
    for _, row in df.iterrows():
        if row["Generate"] != "✅":
            continue
        
        chapter_data = {
            "chapter": int(row["Chapter"]),
            "title": row["Title"],
            "events": {sl: row[sl] for sl in storylines}
        }
        
        print(f"Generating chapter {chapter_data['chapter']}...")
        chapter_text, summary = generator.generate_chapter(
            chapter_data,
            "Generated from outline",
            storylines,
            previous_summaries
        )
        
        filename = f"{settings.CHAPTERS_DIR}/chapter_{chapter_data['chapter']}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(chapter_text)
        
        manager.update_outline(chapter_data['chapter'], summary, filename)
        previous_summaries.append(f"Chapter {chapter_data['chapter']}: {summary}")
        print(f"Chapter {chapter_data['chapter']} generated. Summary: {summary[:50]}...")
    
    print("All chapters generated!")

if __name__ == "__main__":
    main()