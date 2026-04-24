import json
import re

with open('data/parsed_questions.json', 'r', encoding='utf-8') as f:
    text = f.read()

def fix_hindi_answer(match):
    val = match.group(1)
    if val.startswith('-') or val == 'काशी':
        return 'उत्तर' + val
    return 'उत्तर ' + val

text_fixed = re.sub(r'ANSWER:\s*([-\u0900-\u097F]+)', fix_hindi_answer, text)

# Just searching for the exact string ANSWER:
print("Occurrences of ANSWER: ->", text_fixed.count('ANSWER:'))
