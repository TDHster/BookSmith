# BookSmith

AI-powered book generation system that creates complete books from simple descriptions using Google's Gemini AI.

## Features

- **Outline Generation**: Create detailed book outlines with storylines and chapter structure
- **Chapter Generation**: Generate full chapters based on outline and storyline progression
- **Book Compilation**: Compile generated chapters into DOCX format
- **Storyline Tracking**: Maintain consistency across multiple storylines throughout the book

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BookSmith.git
cd BookSmith
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env_example .env
```

4. Configure your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.0-flash
LOG_LEVEL=DEBUG
OUTLINE_FILE=book_outline.xlsx
CHAPTERS_DIR=generated_chapters
```

## Usage

### Generate Book Outline
```bash
python main.py generate_outline --description "A sci-fi thriller about AI consciousness"
```

### Correct Book Outline
You can edit storylines and generate all chapters or individual chapters in the next step by selecting the appropriate field in OUTLINE_FILE.

### Generate Chapters
```bash
python main.py generate_chapters
```

### Compile Book
```bash
python main.py compile_book --title "My Generated Book"
```

## Project Structure

```
BookSmith/
├── cli/                    # Command-line interface modules
├── config/                 # Configuration settings
├── core/                   # Core application logic
├── domain/                 # Business logic and book generation
├── infrastructure/         # External services (LLM client, file management)
├── generated_chapters/     # Generated chapter files
├── books/                  # Compiled book outputs
└── main.py                # Entry point
```

## Requirements

- Python 3.8+
- Google Gemini API key
- Dependencies listed in `requirements.txt`
- a little command line expirience
