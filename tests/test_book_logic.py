#tests/test_book_logic.py
import pytest
from unittest.mock import Mock, patch
import json
from domain.book_logic import BookGenerator


class TestBookGenerator:
    @pytest.fixture
    def mock_llm(self):
        return Mock()
    
    @pytest.fixture
    def book_generator(self, mock_llm):
        return BookGenerator(mock_llm)
    
    def test_generate_plot_success(self, book_generator, mock_llm):
        mock_response = json.dumps({
            "storylines": ["Main Plot", "Romance", "Mystery"],
            "chapters": [
                {
                    "chapter": 1,
                    "title": "The Beginning",
                    "events": {"Main Plot": "Hero starts journey"}
                }
            ]
        })
        mock_llm.generate_text.return_value = mock_response
        
        storylines, chapters = book_generator.generate_plot("Test description")
        
        assert storylines == ["Main Plot", "Romance", "Mystery"]
        assert len(chapters) == 1
        assert chapters[0]["chapter"] == 1
    
    def test_extract_json_valid(self, book_generator):
        json_text = '{"key": "value"}'
        result = book_generator.extract_json(json_text)
        assert result == {"key": "value"}
    
    def test_extract_json_with_code_block(self, book_generator):
        text = '```json\n{"key": "value"}\n```'
        result = book_generator.extract_json(text)
        assert result == {"key": "value"}
    
    def test_generate_chapter_success(self, book_generator, mock_llm):
        mock_response = json.dumps({
            "text": "Chapter content here",
            "summary": "Chapter summary"
        })
        mock_llm.generate_text.return_value = mock_response
        
        chapter_data = {
            "chapter": 1,
            "title": "Test Chapter",
            "events": {"Plot": "Something happens"}
        }
        
        text, summary = book_generator.generate_chapter(
            chapter_data, "Book description", ["Plot"], []
        )
        
        assert text == "Chapter content here"
        assert summary == "Chapter summary"