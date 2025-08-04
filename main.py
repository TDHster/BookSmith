import argparse
from cli.generate_plot import main as generate_plot
from cli.generate_chapters import main as generate_chapters

def main():
    parser = argparse.ArgumentParser(description="Book Generation System")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    plot_parser = subparsers.add_parser("generate_plot", help="Generate book outline")
    plot_parser.add_argument("--description", required=True, help="Book description")
    
    chapter_parser = subparsers.add_parser("generate_chapters", help="Generate book chapters")
    
    args = parser.parse_args()
    
    if args.command == "generate_plot":
        generate_plot(args.description)
    elif args.command == "generate_chapters":
        generate_chapters()

if __name__ == "__main__":
    main()