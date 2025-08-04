import pandas as pd
from pathlib import Path
from config.settings import settings

class OutlineManager:
    def __init__(self):
        self.filename = settings.OUTLINE_FILE
        self.storylines = []
    
    def save_outline(self, storylines: list, chapters: list):
        self.storylines = storylines
        
        data = []
        for ch in chapters:
            row = {
                "Chapter": ch["chapter"],
                "Title": ch["title"],
                "Generate": "✅",
                "Summary": "",
                "File": ""
            }
            for storyline in storylines:
                row[storyline] = ch["events"].get(storyline, "")
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(self.filename, index=False)
        return df
    
    def load_outline(self) -> pd.DataFrame:
        return pd.read_excel(self.filename, engine='openpyxl')
    
    def update_outline(self, chapter_num: int, summary: str, filename: str):
        df = self.load_outline()
        idx = df[df["Chapter"] == chapter_num].index[0]
        
        df.at[idx, "Generate"] = ""
        df.at[idx, "Summary"] = summary
        df.at[idx, "File"] = filename
        
        df.to_excel(self.filename, index=False)