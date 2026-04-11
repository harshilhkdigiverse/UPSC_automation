import os
from parser.parse_docx import main as parse_questions
from automation.playwright_script import run

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)

    # Step 1: Parse docx files → data/parsed_questions.json
    parse_questions()

    # Step 2: Run browser automation
    run()