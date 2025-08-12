import argparse
from infrastructure.llm_client import LLMClientFactory

from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator
from logger import logger

def main(description: str, language: str):
    llm = LLMClientFactory.create_client(language)
    generator = BookGenerator(llm)
    manager = OutlineManager()
    
    logger.info(f"Generating outline with description: {description}")
    storylines, chapters = generator.generate_outline(description)
    manager.save_outline(storylines, chapters)
    logger.info(f"Outline generated and saved to {manager.filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate book outline")
    parser.add_argument("--description", required=True, help="Book description")
    args = parser.parse_args()
    
    main(args.description)