#domain/book_logic.py
import json
import re
from logger import logger 

MAX_RETRIES = 3

class BookGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def generate_outline(self, book_description: str) -> tuple:
        prompt = f"""
            Создай подробную структуру книги на основе этого описания:
            {book_description}

            Верни ТОЛЬКО JSON с такими ключами:
            - "storylines": список названий сюжетных линий (5–7 штук)
            - "chapters": список глав с полями:
                "chapter": номер главы (начиная с 1),
                "title": название главы,
                "events": словарь, где ключи — названия линий, а значения — краткое развитие (по одному предложению)

            Включи от 8 до 12 глав. Обеспечь логичное развитие сюжета по всем линиям.
            """
        
        try:
            result = self.llm.generate_text(prompt)
            if not result or not isinstance(result, str):
                result = "{}"

            # ✅ Используем extract_json
            data = self.extract_json(result)

            if not data:
                raise ValueError("LLM вернул пустой или нечитаемый ответ")

            storylines = data.get("storylines")
            chapters = data.get("chapters")

            if not isinstance(storylines, list) or not isinstance(chapters, list):
                raise ValueError("storylines и chapters должны быть списками")

            if len(storylines) == 0 or len(chapters) == 0:
                raise ValueError("storylines и chapters не могут быть пустыми")

            return storylines, chapters

        except Exception as e:
            logger.error(f"Ошибка при генерации сюжета: {e}")
            raise ValueError("Failed to parse LLM response") from e


    def extract_json(self, text: str) -> dict:
        """Извлекает JSON из текста ответа, обрабатывая различные форматы"""
        if not text or not isinstance(text, str):
            return {}

        # logger.debug(f"🔍 Извлечение JSON из ответа LLM:\n{text[:500]}...")  #  

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Пробуем извлечь из ```json ... ```
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON из блока: {e}")

        # Пробуем найти { ... }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON из фрагмента: {e}")

        logger.error(f"❌ Не удалось извлечь JSON из ответа LLM:\n{text}")
        return {}

    def generate_chapter(
        self, 
        chapter_data: dict, 
        book_description: str, 
        storylines: list,
        previous_summaries: list,
        chapter_length: str = "800-1200 слов"
    ) -> tuple:
        prev_text = "\n".join(previous_summaries) if previous_summaries else "None"
        
        prompt = f"""
            ОПИСАНИЕ КНИГИ: {book_description}

            СЮЖЕТНЫЕ ЛИНИИ: {", ".join(storylines)}

            РЕЗЮМЕ ПРЕДЫДУЩИХ ГЛАВ:
            {prev_text}

            ТРЕБОВАНИЯ К ТЕКУЩЕЙ ГЛАВЕ:
            Глава {chapter_data['chapter']}: {chapter_data['title']}
            Развитие сюжета:
            {json.dumps(chapter_data['events'], indent=2, ensure_ascii=False)}

            Напиши:
            1. Полный текст главы ({chapter_length})
            2. Краткое резюме из трёх предложений — только ключевые события

            ВАЖНО: ВСЁ — НА РУССКОМ ЯЗЫКЕ. НИКАКОГО АНГЛИЙСКОГО.

            Верни ответ в формате JSON:
            {{"text": "полный текст главы", "summary": "резюме из трёх предложений. Если упоминаешь имена, добавь описания, кто это и что представляет."}}
            """
        
        
        for attempt in range(MAX_RETRIES):
            try:
                result = self.llm.generate_text(prompt)
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
            
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
            # error_filename = f"error_chapter_{chapter_data['chapter']}.txt"
            # with open(error_filename, "w", encoding="utf-8") as f:
                # f.write(f"Prompt:\n{prompt}\n\nResponse:\n{result}")
            
            logger.error(f"Error processing chapter {chapter_data['chapter']}: {e}")
            # logger.error(f"Full error response saved to {error_filename}")
            raise ValueError(f"Failed to process chapter response: {e}") from e