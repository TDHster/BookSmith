import google.generativeai as genai
from config.settings import settings

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            settings.MODEL_NAME,
            # system_instruction="You are a professional writer"  # Системная инструкция здесь
            system_instruction="Ты профессиональный писатель на русском языке"  # Системная инструкция здесь
        )
    
    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.7)
        )
        return response.text