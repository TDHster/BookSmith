import google.generativeai as genai
from config.settings import settings
from logger import logger

class GeminiClient:
    def __init__(self, language):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            settings.MODEL_NAME,
            # system_instruction="You are a professional writer"  # Системная инструкция здесь
            system_instruction=f"Ты профессиональный писатель на {language} языке"  # Системная инструкция здесь
        )
    
    def generate_text(self, prompt: str) -> str:
        # Оцениваем длину промпта
        token_count = len(prompt.split())  # Простая оценка
        if token_count > 10000:  # Упрощенная проверка
            logger.warning(f"Long prompt: {token_count} tokens")
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.7)
        )
        return response.text