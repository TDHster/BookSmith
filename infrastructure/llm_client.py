from abc import ABC, abstractmethod
from config.settings import settings

from logger import logger
from typing import Optional


class LLMClient(ABC):
    """Абстрактный интерфейс для LLM клиентов"""
    def __init__(self, language: str):
        self.language = language
    
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Генерирует текст на основе промпта"""
        pass


class GeminiClient(LLMClient):
    """Реализация для Google Gemini"""
    def __init__(self, language: str):
        super().__init__(language)
        import google.generativeai as genai
        self.genai = genai
        self.genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.debug(f'Using language: {language}')
        system_instruction = (
            # f"You are a professional writer creating content in {self.language}, use only {self.language} in answer. "
            # "Respond with well-structured, engaging narratives."

            "Ты — профессиональный писатель, создающий текст на русском языке. Отвечай только на русском. Структурируй ответ чётко и логично, используя живой и увлекательный стиль повествования."
        )
        
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_instruction
        )
    
    def generate_text(self, prompt: str) -> str:
        token_count = len(prompt.split())
        if token_count > 10000:
            logger.warning(f"Long Gemini prompt: {token_count} tokens")
        
        # logger.debug(f'{prompt=}')
        response = self.model.generate_content(
            prompt,
            generation_config=self.genai.GenerationConfig(temperature=0.7)
        )
        return response.text

class OpenAIClient(LLMClient):
    """Реализация для OpenAI ChatGPT"""
    def __init__(self, language: str):
        super().__init__(language)
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_text(self, prompt: str) -> str:
        token_count = len(prompt.split())
        if token_count > 10000:
            logger.warning(f"Long OpenAI prompt: {token_count} tokens")
        
        system_message = {
            "role": "system",
            "content": f"You are a professional writer creating content in {self.language}."
        }
        
        user_message = {
            "role": "user",
            "content": prompt
        }
        
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[system_message, user_message],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content

class LLMClientFactory:
    """Фабрика для создания LLM клиентов"""
    @staticmethod
    def create_client(language: str, provider='gemini') -> LLMClient:
        # provider = settings.LLM_PROVIDER.lower()
        
        if provider == "gemini":
            return GeminiClient(language)
        elif provider == "openai":
            return OpenAIClient(language)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")