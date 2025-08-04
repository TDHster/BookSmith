#domain/book_logic.py
import json

class BookGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def generate_plot(self, book_description: str) -> tuple:
        # Убрали system_instruction из вызова
        prompt = f"""
        Create a detailed book plot based on this description: 
        {book_description}
        
        Return JSON format ONLY with these keys:
        - "storylines": list of storyline names (5-7 items)
        - "chapters": list of chapter details with:
            "chapter": chapter number (start from 1),
            "title": chapter title,
            "events": dict where keys are storyline names and values are 1-sentence developments
        
        Include 8-12 chapters. Ensure logical progression across storylines.
        """
        
        result = self.llm.generate_text(prompt)
        try:
            data = json.loads(result.strip("```json\n").strip("\n```"))
            return data["storylines"], data["chapters"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError("Failed to parse LLM response") from e
    
    def generate_chapter(
        self, 
        chapter_data: dict, 
        book_description: str, 
        storylines: list,
        previous_summaries: list
    ) -> tuple:
        # Убрали system_instruction из вызова
        prev_text = "\n".join(previous_summaries) if previous_summaries else "None"
        
        prompt = f"""
        BOOK DESCRIPTION: {book_description}
        
        STORYLINES: {", ".join(storylines)}
        
        PREVIOUS CHAPTER SUMMARIES:
        {prev_text}
        
        CURRENT CHAPTER REQUIREMENTS:
        Chapter {chapter_data['chapter']}: {chapter_data['title']}
        Events:
        {json.dumps(chapter_data['events'], indent=2)}
        
        Write:
        1. Full chapter text (800-1200 words)
        2. 3-sentence summary of key events
        
        Return in JSON format:
        {{"text": "full chapter text", "summary": "3-sentence summary"}}
        """
        
        result = self.llm.generate_text(prompt)
        try:
            data = json.loads(result.strip("```json\n").strip("\n```"))
            return data["text"], data["summary"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError("Failed to parse chapter response") from e