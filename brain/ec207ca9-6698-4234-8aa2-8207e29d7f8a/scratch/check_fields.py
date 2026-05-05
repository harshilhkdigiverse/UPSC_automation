import json

def check_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    required_root_fields = ['number', 'subtopic', 'category', 'question_type', 'english', 'hindi']
    required_lang_fields = ['number', 'subtopic', 'category', 'question_type', 'question', 'question_image', 'statements', 'pairs', 'lastQuestion', 'options', 'options_images', 'answer', 'solution', 'solution_image']
    
    issues = []
    
    for i, item in enumerate(data):
        q_num = item.get('number', f'Index {i}')
        
        # Check root fields
        for field in required_root_fields:
            if field not in item:
                issues.append(f"Question {q_num}: Missing root field '{field}'")
        
        # Check English and Hindi sections
        for lang in ['english', 'hindi']:
            lang_data = item.get(lang)
            if not lang_data:
                issues.append(f"Question {q_num}: Missing '{lang}' section")
                continue
            
            for field in required_lang_fields:
                if field not in lang_data:
                    issues.append(f"Question {q_num}: Missing field '{field}' in '{lang}'")
            
            # Check options
            options = lang_data.get('options', {})
            for opt in ['A', 'B', 'C', 'D']:
                if opt not in options:
                    issues.append(f"Question {q_num}: Missing option '{opt}' in '{lang}'")
                elif not options[opt]:
                    # Empty options might be okay in some cases, but usually they should have text
                    pass
            
            # Check answer
            if not lang_data.get('answer'):
                issues.append(f"Question {q_num}: Missing or empty 'answer' in '{lang}'")
                
            # Check solution
            if not lang_data.get('solution'):
                issues.append(f"Question {q_num}: Missing or empty 'solution' in '{lang}'")

    if not issues:
        print("No missing fields found.")
    else:
        for issue in issues:
            print(issue)

if __name__ == "__main__":
    check_json(r'd:\UPSC_automation\data\parsed_questions.json')
