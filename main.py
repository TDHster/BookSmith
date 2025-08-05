#!./venv/bin/python
import argparse
from cli.generate_outline import main as generate_outline
from cli.generate_chapters import main as generate_chapters
from cli.compile_book import compile_book

def main():
    parser = argparse.ArgumentParser(description="Book Generation System")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    plot_parser = subparsers.add_parser("generate_outline", help="Generate book outline")
    plot_parser.add_argument("--description", required=True, help="Book description")
    plot_parser.add_argument("--language", default="Русский", help="Book language")
    
    chapter_parser = subparsers.add_parser("generate_chapters", help="Generate book chapters")
    chapter_parser.add_argument("--language", default="Русский", help="Book language")
    
    compile_parser = subparsers.add_parser("compile_book", help="Compile book to DOCX")
    compile_parser.add_argument("--title", help="Custom book title (optional)") 
    
    args = parser.parse_args()
    
    if args.command == "generate_outline":
        generate_outline(args.description, args.language)
    elif args.command == "generate_chapters":
        generate_chapters(args.language)
    elif args.command == "compile_book":
        compile_book(args.title)
        
if __name__ == "__main__":
    main()