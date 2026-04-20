"""
parse_docx.py - V3 Robust
"""
import docx
import json
import re
import os

# Use a very specific marker that won't conflict with anything
IMG_START = "[[IMG_START]]"
IMG_END = "[[IMG_END]]"

def extract_field(text: str) -> dict:
    pattern = re.escape(IMG_START) + r"\s*(.*?)\s*" + re.escape(IMG_END)
    m = re.search(pattern, text, re.I)
    
    # Extract only the first image path found
    image_path = m.group(1).strip() if m else ""
    
    # Remove ALL instances of the image marker from the text
    clean_text = re.sub(pattern, '', text, flags=re.I).strip()
    
    return {
        "text": clean_text,
        "image": image_path
    }

def parse_block_regex(text: str) -> dict | None:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 4: return None

    q_marker = r'(?:\(\d+\)|\d+\s*[\.\)\:])'
    pattern = re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*' + q_marker + r'|^' + q_marker
    
    q_idx = -1
    for idx, line in enumerate(lines):
        if re.match(pattern, line):
            q_idx = idx
            break
    
    if q_idx == -1: return None
    
    meta = lines[:q_idx]
    subtopic = meta[0] if len(meta) > 0 else "Unknown"
    category = meta[1].lower() if len(meta) > 1 else "aptitude"
    # Normalize question_type: lower case and replace spaces with hyphens (e.g., "Normal Csat" -> "normal-csat")
    question_type = meta[2].lower().strip().replace(" ", "-") if len(meta) > 2 else "normal"

    i = q_idx
    question_lines = []
    # Remove question marker like (1) or 1.
    first_q_line = re.sub(r'^(?:' + re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*)?(?:\(\d+\)|\d+\s*[\.\)\:])\s*', '', lines[i]).strip()
    question_lines.append(first_q_line)
    i += 1

    is_options = lambda s: bool(re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*[:\)])', s, re.I))
    is_pair = lambda s: bool(re.match(r'^(?:Pair\s*\d+\s*:|.*?\s*=\s*.*)', s, re.I))
    is_stmt = lambda s: bool(re.match(r'^\d+\s*[\.\)]', s, re.I))
    is_ans = lambda s: bool(re.search(r'Answer\s*:', s, re.I))
    is_sol = lambda s: bool(re.search(r'Solution\s*:', s, re.I))

    # 1. Question text starts at q_idx
    # We want to separate the main question text from statements/pairs.
    
    # Trigger patterns
    stmt_trigger = r'consider\b.*?statements|निम्नलिखित\b.*?कथन'
    pair_trigger = r'consider\b.*?pairs|निम्नलिखित\b.*?युग्म'
    lq_trigger = r'(?:Which|Correct|Choose|Incorrect)\b.*?(?:statements|pairs|option|options)\b.*?(?:correct|true|false|matches|matching)|उपरोक्त\b.*?(?:कथन|युग्म)\b.*?(?:सही|गलत|कितने)'

    i = q_idx
    question_lines = []
    
    # First line (with number)
    first_q_line = re.sub(r'^(?:' + re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*)?(?:\(\d+\)|\d+\.)\s*', '', lines[i]).strip()
    question_lines.append(first_q_line)
    i += 1

    # Logic to collect question text until statements or options
    is_stmt_mode = "statement" in question_type
    is_pair_mode = "pair" in question_type

    while i < len(lines):
        if is_options(lines[i]) or is_ans(lines[i]): break
        
        # If we see a statement-like number (1., 2.), and we are in statement mode,
        # it might be the start of statements. 
        # But we also look for the "Consider the following..." header.
        if is_stmt_mode and (is_stmt(lines[i]) or re.search(stmt_trigger, question_lines[-1], re.I)):
             if not re.search(stmt_trigger, lines[i], re.I): # Don't break if this line IS the trigger
                break
        if is_pair_mode and (is_pair(lines[i]) or re.search(pair_trigger, question_lines[-1], re.I)):
            if not re.search(pair_trigger, lines[i], re.I):
                break

        question_lines.append(lines[i])
        i += 1

    statements = []
    pairs = []
    lastQuestion = ""

    if is_stmt_mode:
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]) and not re.search(lq_trigger, lines[i], re.I):
            text = re.sub(r'^\d+[\.\)]\s*', '', lines[i]).strip()
            if text: statements.append(extract_field(text))
            i += 1
        lq_parts = []
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = extract_field(' '.join(lq_parts).strip())
    elif is_pair_mode:
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]) and not re.search(lq_trigger, lines[i], re.I):
            # Check if it's a pair line (contains =)
            if '=' in lines[i]:
                row = [extract_field(p.strip()) for p in re.split(r'\s*=\s*', lines[i])]
                if len(row) >= 2: pairs.append(row)
            else:
                # If not a pair line but in pair mode, might be a header or leftover text
                # For now just skip or add to question? Let's skip.
                pass
            i += 1
        lq_parts = []
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = extract_field(' '.join(lq_parts).strip())
    else:
        # Normal type: question text already collected until options
        pass

    question_field = extract_field('\n'.join(question_lines))

    # Options
    options = {}
    options_images = {}
    opt_map = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'}
    
    while i < len(lines) and not is_ans(lines[i]):
        line = lines[i]
        # Robust marker: Check if line starts with marker or has marker after substantial space
        # And ensure we don't match inside IMG tags by checking the left context
        matches = []
        # Find all potential matches
        for m in re.finditer(r'(?:\(([a-dA-D])\)|\b([a-dA-D])\s*:)', line, re.I):
            # Check if this match is inside an IMG tag
            pre = line[:m.start()]
            if pre.count(IMG_START) > pre.count(IMG_END):
                continue # Inside tag
            matches.append(m)
        
        if matches:
            for idx_m, m in enumerate(matches):
                letter = (m.group(1) or m.group(2)).lower()
                start_text = m.end()
                end_text = matches[idx_m+1].start() if idx_m+1 < len(matches) else len(line)
                text_opt = line[start_text:end_text].strip()
                field = extract_field(text_opt)
                options[opt_map[letter]] = field["text"]
                options_images[opt_map[letter]] = field["image"]
            i += 1
        elif options and not is_stmt(line) and not is_pair(line) and not is_ans(line):
            last_l = sorted(options.keys())[-1]
            ext = extract_field(line)
            options[last_l] += " " + ext["text"]
            if ext["image"]: options_images[last_l] = ext["image"]
            i += 1
        else:
            break

    # Answer
    answer = ''
    while i < len(lines) and not is_sol(lines[i]):
        am = re.search(r'Answer\s*:\s*\(?([a-dA-D])\)?', lines[i], re.I)
        if am:
            answer = am.group(1).lower()
        i += 1

    # Solution
    solution_lines = []
    while i < len(lines):
        sm = re.search(r'Solution\s*:\s*(.*)', lines[i], re.I)
        if sm:
            solution_lines.append(sm.group(1).strip())
            i += 1
            while i < len(lines):
                solution_lines.append(lines[i])
                i += 1
            break
        i += 1
    solution_field = extract_field('\n'.join(solution_lines))

    return {
        "subtopic": subtopic,
        "category": category if category != "aptitude" else "concept",
        "question_type": question_type,
        "question": question_field["text"],
        "question_image": question_field["image"],
        "statements": statements,
        "pairs": pairs,
        "lastQuestion": lastQuestion if isinstance(lastQuestion, dict) else {"text": lastQuestion, "image": ""},
        "options": options,
        "options_images": options_images,
        "answer": answer,
        "solution": solution_field["text"],
        "solution_image": solution_field["image"]
    }

def normalise(q: dict) -> dict | None:
    if not q["question"] and not q["question_image"]: return None
    if len(q["options"]) < 4: return None
    if not q["answer"]: return None
    return q

def parse_docx_file(file_path: str) -> list:
    doc = docx.Document(file_path)
    img_dir = "data/images"
    os.makedirs(img_dir, exist_ok=True)
    img_map = {r_id: rel.target_part for r_id, rel in doc.part.rels.items() if 'image' in rel.reltype}

    lines = []
    for p in doc.paragraphs:
        p_text = ''
        for run in p.runs:
            p_text += run.text
            xml = run._element.xml
            if '<w:drawing>' in xml:
                m = re.search(r'r:embed=\"(rId\d+)\"', xml)
                if m and m.group(1) in img_map:
                    img_part = img_map[m.group(1)]
                    fname = img_part.partname.split('/')[-1]
                    out_path = os.path.join(img_dir, fname)
                    with open(out_path, 'wb') as f: f.write(img_part.blob)
                    clean_p = os.path.abspath(out_path).replace('\\', '/')
                    p_text += f" {IMG_START}{clean_p}{IMG_END} "
        for sl in p_text.split('\n'):
            if sl.strip(): lines.append(sl.strip())

    # Hybrid block detection
    block_starts = []
    
    # 1. Triplet-based detection
    triplet_starts = set()
    for j in range(1, len(lines)):
        l_j = lines[j].lower()
        l_j_prev = lines[j-1].lower()
        if (l_j == "normal" or l_j == "statement" or l_j == "pair") and "concept" in l_j_prev:
            triplet_starts.add(max(0, j - 2))
    
    # 2. Sequential/Contextual detection
    # Any line matching the question marker that follows a solution block
    q_marker_re = r'(?:' + re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*)?(?:\(\d+\)|(\d+)\s*[\.\)\:])'
    
    last_q_val = 0
    in_solution = False
    
    for i, line in enumerate(lines):
        # Triplet always wins
        if i in triplet_starts:
            block_starts.append(i)
            # Find the number in this block to keep sequence
            for k in range(i, min(i+10, len(lines))):
                m = re.match(q_marker_re, lines[k])
                if m and m.group(1):
                    last_q_val = int(m.group(1))
                    break
            in_solution = False
            continue
            
        # Check for solution marker
        if "answer:" in line.lower() or "solution:" in line.lower() or "विकल्प" in line or "सही है" in line:
            in_solution = True
            
        # Check for question number fallback
        m = re.match(q_marker_re, line)
        if m:
            q_val_str = m.group(1)
            if q_val_str:
                q_val = int(q_val_str)
                # It's a new question if it's the next in sequence or follows a solution
                if (q_val == last_q_val + 1) or (in_solution and q_val > last_q_val):
                    # Only add if not already captured by a nearby triplet
                    is_new = True
                    for s in block_starts:
                        if abs(s - i) < 10:
                            is_new = False
                            break
                    if is_new:
                        block_starts.append(i)
                        last_q_val = q_val
                        in_solution = False

    # Filter and refine: each block must contain a question number
    final_block_starts = sorted(list(set(block_starts)))
    
    questions = []
    for idx in range(len(final_block_starts)):
        start = final_block_starts[idx]
        end = final_block_starts[idx+1] if idx+1 < len(final_block_starts) else len(lines)
        q = parse_block_regex('\n'.join(lines[start:end]))
        if q:
            nq = normalise(q)
            if nq: questions.append(nq)
            
    print(f"Parsed {len(questions)} questions from {os.path.basename(file_path)}")
    return questions

def merge_questions(en_qs: list, hi_qs: list) -> list:
    merged = []
    max_len = max(len(en_qs), len(hi_qs))
    for i in range(max_len):
        en_q = en_qs[i] if i < len(en_qs) else None
        hi_q = hi_qs[i] if i < len(hi_qs) else None
        
        # Definitive metadata from English
        ref = en_q or hi_q
        subtopic = ref.get("subtopic", "Unknown")
        category = ref.get("category", "concept")
        if category == "aptitude": category = "concept"
        q_type = ref.get("question_type", "normal")

        def build_side(q_data, definitive_meta):
            if not q_data:
                return {
                    "subtopic": definitive_meta["subtopic"],
                    "category": definitive_meta["category"],
                    "question_type": definitive_meta["type"],
                    "question": "", "question_image": "",
                    "statements": [], "pairs": [], "lastQuestion": {"text": "", "image": ""},
                    "options": {"A":"","B":"","C":"","D":""},
                    "options_images": {"A":"","B":"","C":"","D":""},
                    "answer": "", "solution": "", "solution_image": ""
                }
            # Sync metadata
            q_data["subtopic"] = definitive_meta["subtopic"]
            q_data["category"] = definitive_meta["category"]
            q_data["question_type"] = definitive_meta["type"]
            return q_data

        meta_bundle = {"subtopic": subtopic, "category": category, "type": q_type}
        
        merged.append({
            "subtopic": subtopic,
            "category": category,
            "question_type": q_type,
            "english": build_side(en_q, meta_bundle),
            "hindi": build_side(hi_q, meta_bundle)
        })
    return merged

def main():
    # Ensure the script runs from the project root
    script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(script_path))
    os.chdir(project_root)
    
    os.makedirs("data", exist_ok=True)
    en = parse_docx_file("data/english.docx")
    hi = parse_docx_file("data/hindi.docx")
    merged = merge_questions(en, hi)
    with open("data/parsed_questions.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"DONE: Parsed {len(merged)} questions.")

if __name__ == "__main__":
    main()
