import argparse
from infrastructure.llm_client import GeminiClient
from infrastructure.outline_manager import OutlineManager
from domain.book_logic import BookGenerator

def main(description: str):
    llm = GeminiClient()
    generator = BookGenerator(llm)
    manager = OutlineManager()
    
    print("Generating plot...")
    storylines, chapters = generator.generate_plot(description)
    manager.save_outline(storylines, chapters)
    print(f"Plot generated and saved to {manager.filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate book outline")
    parser.add_argument("--description", required=True, help="Book description")
    args = parser.parse_args()
    
    main(args.description)