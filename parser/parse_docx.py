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

    q_idx = -1
    for idx, line in enumerate(lines):
        if re.match(r'^(?:' + re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*)?\(\d+\)', line):
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
    first_q_line = re.sub(r'^\(\d+\)\s*', '', lines[i]).strip()
    question_lines.append(first_q_line)
    i += 1

    is_options = lambda s: bool(re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', s, re.I))
    is_pair = lambda s: bool(re.match(r'^Pair\s*\d+\s*:', s, re.I))
    is_stmt = lambda s: bool(re.match(r'^\d+\.', s, re.I))
    is_ans = lambda s: bool(re.search(r'Answer\s*:', s, re.I))
    is_sol = lambda s: bool(re.search(r'Solution\s*:', s, re.I))

    while i < len(lines) and not is_options(lines[i]) and not is_pair(lines[i]) and not is_stmt(lines[i]) and not is_ans(lines[i]):
        question_lines.append(lines[i])
        i += 1

    statements = []
    pairs = []
    lastQuestion = ""

    if "statement" in question_type:
        while i < len(lines) and is_stmt(lines[i]):
            stmt_text = re.sub(r'^\d+\.\s*', '', lines[i]).strip()
            statements.append(extract_field(stmt_text))
            i += 1
        lq_parts = []
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = ' '.join(lq_parts).strip()
    elif question_type == "pair":
        while i < len(lines) and is_pair(lines[i]):
            pair_line = re.sub(r'^Pair\s*\d+\s*:\s*', '', lines[i], flags=re.I).strip()
            row = [extract_field(p.strip()) for p in re.split(r'\s*=\s*', pair_line)]
            pairs.append(row)
            i += 1
        lq_parts = []
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = ' '.join(lq_parts).strip()
    else:
        while i < len(lines) and not is_options(lines[i]) and not is_ans(lines[i]):
            question_lines.append(lines[i])
            i += 1

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
        "category": category,
        "question_type": question_type,
        "question": question_field["text"],
        "question_image": question_field["image"],
        "statements": statements,
        "pairs": pairs,
        "lastQuestion": lastQuestion,
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

    block_starts = []
    for i, line in enumerate(lines):
        if re.match(r'^(?:' + re.escape(IMG_START) + r'.*?' + re.escape(IMG_END) + r'\s*)?\(\d+\)', line):
            block_starts.append(max(0, i - 3))
    
    questions = []
    for idx in range(len(block_starts)):
        start = block_starts[idx]
        end = block_starts[idx+1] if idx+1 < len(block_starts) else len(lines)
        q = parse_block_regex('\n'.join(lines[start:end]))
        if q:
            nq = normalise(q)
            if nq: questions.append(nq)
    return questions

def merge_questions(en_qs: list, hi_qs: list) -> list:
    merged = []
    max_len = max(len(en_qs), len(hi_qs))
    for i in range(max_len):
        en_q = en_qs[i] if i < len(en_qs) else None
        hi_q = hi_qs[i] if i < len(hi_qs) else None
        ref = en_q or hi_q
        def build_side(q_data):
            if not q_data:
                return {
                    "question": "", "question_image": "",
                    "statements": [], "pairs": [], "lastQuestion": "",
                    "options": {"A":"","B":"","C":"","D":""},
                    "options_images": {"A":"","B":"","C":"","D":""},
                    "answer": "", "solution": "", "solution_image": ""
                }
            return q_data
        merged.append({
            "subtopic": ref["subtopic"],
            "category": ref["category"],
            "question_type": ref["question_type"],
            "english": build_side(en_q),
            "hindi": build_side(hi_q)
        })
    return merged

def main():
    os.makedirs("data", exist_ok=True)
    en = parse_docx_file("data/english.docx")
    hi = parse_docx_file("data/hindi.docx")
    merged = merge_questions(en, hi)
    with open("data/parsed_questions.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"DONE: Parsed {len(merged)} questions.")

if __name__ == "__main__":
    main()
