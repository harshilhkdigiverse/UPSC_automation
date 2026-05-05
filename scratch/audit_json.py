
import json

def audit_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = len(data)
    print(f"Total Questions: {total}")
    
    issues = []
    for q in data:
        q_num = q.get('number', '??')
        q_type = q.get('question_type', 'normal')
        
        # Check English
        en = q.get('english', {})
        if len(en.get('options', {})) != 4:
            issues.append(f"Q{q_num}: English options count is {len(en.get('options', {}))}")
        if q_type == 'statement' and len(en.get('statements', [])) == 0:
            issues.append(f"Q{q_num}: Type is 'statement' but English statements list is empty")
        if q_type == 'pair' and len(en.get('pairs', [])) == 0:
            issues.append(f"Q{q_num}: Type is 'pair' but English pairs list is empty")
        if not en.get('answer'):
            issues.append(f"Q{q_num}: English answer is empty")
        
        # Check Hindi
        hi = q.get('hindi', {})
        if len(hi.get('options', {})) != 4:
            issues.append(f"Q{q_num}: Hindi options count is {len(hi.get('options', {}))}")
        if q_type == 'statement' and len(hi.get('statements', [])) == 0:
            issues.append(f"Q{q_num}: Type is 'statement' but Hindi statements list is empty")
        if q_type == 'pair' and len(hi.get('pairs', [])) == 0:
            issues.append(f"Q{q_num}: Type is 'pair' but Hindi pairs list is empty")
        if not hi.get('answer'):
            issues.append(f"Q{q_num}: Hindi answer is empty")

        # Logic checks
        if en.get('answer') and hi.get('answer') and en['answer'].lower() != hi['answer'].lower():
            issues.append(f"Q{q_num}: Answer mismatch (EN: {en['answer']}, HI: {hi['answer']})")

    if not issues:
        print("PASS: No structural issues or mismatches found.")
    else:
        print(f"FAIL: Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")

if __name__ == '__main__':
    audit_json('data/parsed_questions.json')
