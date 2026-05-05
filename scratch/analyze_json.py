import json

with open('data/parsed_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total questions: {len(data)}")

missing_info = []

for q in data:
    q_num = q.get("number", "Unknown")
    
    for lang in ["english", "hindi"]:
        lang_data = q.get(lang, {})
        
        if not lang_data:
            missing_info.append(f"Question {q_num}: {lang.capitalize()} object is missing entirely.")
            continue
            
        # Check basic fields
        if not lang_data.get("question", "").strip():
            missing_info.append(f"Question {q_num} ({lang}): 'question' is empty.")
            
        options = lang_data.get("options", {})
        if not options:
            missing_info.append(f"Question {q_num} ({lang}): 'options' object is missing.")
        else:
            for opt in ["A", "B", "C", "D"]:
                if not options.get(opt, "").strip():
                    missing_info.append(f"Question {q_num} ({lang}): Option {opt} is empty.")
        
        if not lang_data.get("answer", "").strip():
            missing_info.append(f"Question {q_num} ({lang}): 'answer' is empty.")
            
        if not lang_data.get("solution", "").strip():
            missing_info.append(f"Question {q_num} ({lang}): 'solution' is empty.")

if not missing_info:
    print("All fields (question, options A-D, answer, solution) are present for all questions.")
else:
    print("\nMissing Fields Found:")
    for m in missing_info:
        print(f"- {m}")

# Check sequence
nums = []
for q in data:
    try:
        nums.append(int(q["number"]))
    except:
        pass
nums.sort()
print(f"\nQuestion numbers found: {nums}")
expected = list(range(1, 51))
missing_nums = set(expected) - set(nums)
if missing_nums:
    print(f"Missing question numbers: {sorted(list(missing_nums))}")
else:
    print("All question numbers from 1 to 50 are present.")
