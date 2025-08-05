import pytest
from unittest.mock import Mock, patch
from infrastructure.llm_client import GeminiClient


class TestGeminiClient:
    @patch('infrastructure.llm_client.genai')
    def test_init(self, mock_genai):
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("English")
        
        mock_genai.configure.assert_called_once()
        mock_genai.GenerativeModel.assert_called_once()
        assert client.model == mock_model
    
    @patch('infrastructure.llm_client.genai')
    def test_generate_text(self, mock_genai):
        mock_response = Mock()
        mock_response.text = "Generated text"
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient("English")
        result = client.generate_text("Test prompt")
        
        assert result == "Generated text"
        mock_model.generate_content.assert_called_once()