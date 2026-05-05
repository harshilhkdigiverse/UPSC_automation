import json
import os

file_path = r'd:\UPSC_automation\data\parsed_questions.json'
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        numbers = [q['number'] for q in data]
        en_empty = [q['number'] for q in data if not q['english'].get('question')]
        hi_empty = [q['number'] for q in data if not q['hindi'].get('question')]
        print(f"Total questions in JSON: {len(data)}")
        print("Raw numbers found:", numbers)
        print("Questions missing English text:", en_empty)
        print("Questions missing Hindi text:", hi_empty)
else:
    print("File not found")
