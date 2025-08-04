#domain/book_logic.py
import json
import re
import logging

logger = logging.getLogger(__name__)


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
    
    def extract_json(self, text: str) -> dict:
        """Извлекает JSON из текста ответа, обрабатывая различные форматы"""
        try:
            # Пытаемся распарсить весь ответ как JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # Если не получилось, пробуем извлечь JSON из блока кода
            match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    logger.error(f"JSON extraction failed: {e}\nText: {text[:500]}...")
            
            # Пробуем найти начало и конец JSON вручную
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    return json.loads(text[start_idx:end_idx+1])
                except json.JSONDecodeError as e:
                    logger.error(f"Manual JSON extraction failed: {e}")
        
        # Если ничего не помогло, логируем и возвращаем пустой словарь
        logger.error(f"Failed to extract JSON from response:\n{text[:1000]}...")
        return {}
    
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
            # Используем улучшенный парсинг JSON
            data = self.extract_json(result)
            
            if not data:
                raise ValueError("Empty JSON response")
            
            # Проверяем наличие обязательных полей
            if "text" not in data or "summary" not in data:
                raise KeyError("Missing required fields in response")
            
            return data["text"], data["summary"]
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            # Сохраняем проблемный ответ для отладки
            error_filename = f"error_chapter_{chapter_data['chapter']}.txt"
            with open(error_filename, "w", encoding="utf-8") as f:
                f.write(f"Prompt:\n{prompt}\n\nResponse:\n{result}")
            
            logger.error(f"Error processing chapter {chapter_data['chapter']}: {e}")
            logger.error(f"Full error response saved to {error_filename}")
            raise ValueError(f"Failed to process chapter response: {e}") from e