import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key',
        'MODEL_NAME': 'test_model',
        'LOG_LEVEL': 'DEBUG',
        'OUTLINE_FILE': 'test_outline.xlsx',
        'CHAPTERS_DIR': 'test_chapters',
        'DEFAULT_LANGUAGE': 'English'
    }):
        yield