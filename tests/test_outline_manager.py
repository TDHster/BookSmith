#tests/test_outline_manager.py
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from infrastructure.outline_manager import OutlineManager


class TestOutlineManager:
    @pytest.fixture
    def outline_manager(self):
        return OutlineManager()
    
    def test_save_outline(self, outline_manager):
        storylines = ["Plot A", "Plot B"]
        chapters = [
            {
                "chapter": 1,
                "title": "Chapter 1",
                "events": {"Plot A": "Event A1", "Plot B": "Event B1"}
            }
        ]
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            df = outline_manager.save_outline(storylines, chapters)
            
            assert len(df) == 1
            assert df.iloc[0]["Chapter"] == 1
            assert df.iloc[0]["Title"] == "Chapter 1"
            assert df.iloc[0]["Plot A"] == "Event A1"
            mock_to_excel.assert_called_once()
    
    @patch('pandas.read_excel')
    def test_load_outline(self, mock_read_excel, outline_manager):
        mock_df = pd.DataFrame({"Chapter": [1], "Title": ["Test"]})
        mock_read_excel.return_value = mock_df
        
        result = outline_manager.load_outline()
        
        assert result.equals(mock_df)
        mock_read_excel.assert_called_once()
    
    @patch('pandas.DataFrame.to_excel')
    @patch('infrastructure.outline_manager.OutlineManager.load_outline')
    def test_update_outline(self, mock_load, mock_to_excel, outline_manager):
        mock_df = pd.DataFrame({
            "Chapter": [1, 2],
            "Generate": ["✅", "✅"],
            "Summary": ["", ""],
            "File": ["", ""]
        })
        mock_load.return_value = mock_df
        
        outline_manager.update_outline(1, "Test summary", "test.txt")
        
        mock_to_excel.assert_called_once()