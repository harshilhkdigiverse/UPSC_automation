"""
parse_docx.py
Parse UPSC question DOCX files using Ollama (llama3.2:3b) for intelligent extraction.
Falls back to regex parsing if Ollama is unavailable.
"""
import docx
import json
import re
import os

# Fallback regex parser
# ---------------------------------------------------------------------------

def extract_field(text: str) -> dict:
    """Extracts an embedded image marker yielding a separate text and image field."""
    m = re.search(r'\[IMAGE:\s*(.*?)\]', text, re.I)
    if m:
        return {
            "text": text.replace(m.group(0), '').strip(),
            "image": m.group(1).strip()
        }
    return {"text": text.strip(), "image": ""}

def parse_block_regex(text: str) -> dict | None:
    """Simple regex-based parser as fallback when Ollama is unavailable."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 6:
        return None

    subtopic = lines[0]
    category = lines[1].lower()
    question_type = lines[2]  # Normal / Statement / etc.

    i = 3
    # Skip the question number prefix like "(1) " or "(2) "
    question_lines = []
    first = re.sub(r'^\(\d+\)\s*', '', lines[i]).strip()
    question_lines.append(first)
    i += 1

    # Collect until we hit numbered statements, pairs, or options
    while i < len(lines) and not re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', lines[i], re.I) \
            and not re.match(r'^Pair\s*\d+\s*:', lines[i], re.I) \
            and not re.match(r'^\d+\.', lines[i]):
        question_lines.append(lines[i])
        i += 1

    statements = []
    pairs = []
    lastQuestion = ""

    if question_type.lower() in ("statement", "statement-csat"):
        # Preamble is accumulated so far
        # Collect numbered statements (1. ..., 2. ...)
        stmt_lines = []
        while i < len(lines) and re.match(r'^\d+\.', lines[i]):
            stmt_text = re.sub(r'^\d+\.\s*', '', lines[i]).strip()
            stmt_lines.append(extract_field(stmt_text))
            i += 1
        statements = stmt_lines


        # Collect lastQuestion (lines until options)
        lq_parts = []
        while i < len(lines) and not re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', lines[i], re.I):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = ' '.join(lq_parts).strip()
        
    elif question_type.lower() == "pair":
        # Extract Pairs (Pair 1: col1 = col2 = col3)
        while i < len(lines) and re.match(r'^Pair\s*\d+\s*:', lines[i], re.I):
            pair_line = re.sub(r'^Pair\s*\d+\s*:\s*', '', lines[i], flags=re.I).strip()
            # Split by equals sign into any number of columns with robust image structures
            parts = [extract_field(p.strip()) for p in re.split(r'\s*=\s*', pair_line)]
            pairs.append(parts)
            i += 1
            
        # Collect lastQuestion (lines until options)
        lq_parts = []
        while i < len(lines) and not re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', lines[i], re.I):
            lq_parts.append(lines[i])
            i += 1
        lastQuestion = ' '.join(lq_parts).strip()
        
    else:
        # Normal: continue collecting question until options
        while i < len(lines) and not re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', lines[i], re.I):
            question_lines.append(lines[i])
            i += 1

    question_text = '\n'.join([l for l in question_lines if l]).strip()

    # Options
    options = {}
    options_images = {}
    opt_map = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'}
    while i < len(lines):
        m = re.match(r'^(?:\(([a-dA-D])\)|\b([a-dA-D])\s*:)\s*(.*)', lines[i], re.I)
        if m:
            letter = (m.group(1) or m.group(2)).lower()
            text_opt = m.group(3).strip()
            i += 1
            while i < len(lines) and not re.match(r'^(?:\([a-dA-D]\)|[A-D]\s*:)', lines[i], re.I) \
                    and not re.match(r'^Answer\s*:', lines[i], re.I):
                text_opt += ' ' + lines[i]
                i += 1
                
            opt_field = extract_field(text_opt)
            options[opt_map[letter]] = opt_field["text"]
            options_images[opt_map[letter]] = opt_field["image"]
        else:
            break

    # Answer
    answer = ''
    while i < len(lines):
        am = re.match(r'^Answer\s*:\s*(?:\()?([a-dA-D])(?:\))?', lines[i], re.I)
        if am:
            answer = am.group(1).lower()
            i += 1
            break
        i += 1

    # Solution
    solution_lines = []
    while i < len(lines):
        sm = re.match(r'^Solution\s*:\s*(.*)', lines[i], re.I)
        if sm:
            first_sol_val = sm.group(1).strip()
            if first_sol_val:
                solution_lines.append(first_sol_val)
            i += 1
            while i < len(lines):
                solution_lines.append(lines[i])
                i += 1
            break
        i += 1
    solution = ' '.join(solution_lines).strip()

    solution_field = extract_field(solution)
    question_field = extract_field(question_text)

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


# ---------------------------------------------------------------------------
# Normalise & validate the extracted dict
# ---------------------------------------------------------------------------

def normalise(q: dict) -> dict | None:
    """Ensure required fields exist and are clean."""
    required = ["subtopic", "category", "question_type", "question", "options", "answer", "solution"]
    for key in required:
        if key not in q:
            print(f"  [WARN] Missing field: {key}")
            return None

    # Defaults for optional fields
    q.setdefault("statements", [])
    q.setdefault("pairs", [])
    q.setdefault("lastQuestion", "")

    # Clean up
    q["category"] = q["category"].lower().strip()
    q["answer"] = q["answer"].lower().strip()

    # Validate answer is a single letter
    if q["answer"] not in ("a", "b", "c", "d"):
        print(f"  [WARN] Invalid answer: {q['answer']!r}")
        return None

    # Fix option keys to be uppercase
    if "options" in q:
        new_options = {}
        for k, v in q["options"].items():
            new_options[k.upper()] = v
        q["options"] = new_options

    if len(q.get("options", {})) < 4:
        print(f"  [WARN] Only {len(q['options'])} options found")
        return None

    return q


# ---------------------------------------------------------------------------
# Language-agnostic block parser
# ---------------------------------------------------------------------------

def parse_block(text: str) -> dict | None:
    q = parse_block_regex(text)

    if q is None:
        return None

    return normalise(q)


# ---------------------------------------------------------------------------
# Merge English + Hindi question dicts
# ---------------------------------------------------------------------------

def merge_questions(en_questions: list, hi_questions: list) -> list:
    """Combine English and Hindi question dicts into final structure."""
    merged = []
    for i, en_q in enumerate(en_questions):
        hi_q = hi_questions[i] if i < len(hi_questions) else None

        entry = {
            "subtopic": en_q["subtopic"],
            "category": en_q["category"],
            "question_type": en_q["question_type"],
            "english": {
                "question": en_q["question"],
                "statements": en_q.get("statements", []),
                "pairs": en_q.get("pairs", []),
                "lastQuestion": en_q.get("lastQuestion", ""),
                "options": en_q["options"],
                "answer": en_q["answer"],
                "solution": en_q["solution"],
            },
            "hindi": {
                "question": hi_q["question"] if hi_q else "",
                "statements": hi_q.get("statements", []) if hi_q else [],
                "pairs": hi_q.get("pairs", []) if hi_q else [],
                "lastQuestion": hi_q.get("lastQuestion", "") if hi_q else "",
                "options": hi_q["options"] if hi_q else {"A": "", "B": "", "C": "", "D": ""},
                # Hindi answer is always same as English (per website docs)
                "answer": en_q["answer"],
                "solution": hi_q["solution"] if hi_q else "",
            },
        }
        merged.append(entry)
    return merged


# ---------------------------------------------------------------------------
# Main docx parser
# ---------------------------------------------------------------------------

def extract_text_with_images(docx_path: str, img_dir="data/images") -> list:
    doc = docx.Document(docx_path)
    os.makedirs(img_dir, exist_ok=True)
    
    img_map = {}
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.reltype:
            img_filename = rel.target_part.partname.split('/')[-1]
            out_path = os.path.abspath(os.path.join(img_dir, img_filename)).replace('\\', '/')
            # Write image bytes
            with open(out_path, "wb") as f:
                f.write(rel.target_part.blob)
            img_map[rel_id] = out_path

    lines = []
    for p in doc.paragraphs:
        xml = p._element.xml
        # Find either <w:t ...>text</w:t> or r:embed="rIdX"
        tokens = re.findall(r'(<w:t[^>]*>.*?</w:t>|r:embed="rId\d+")', xml)
        
        para_str = ""
        for token in tokens:
            if token.startswith('r:embed'):
                rid = re.search(r'rId\d+', token).group(0)
                if rid in img_map:
                    para_str += f" [IMAGE: {img_map[rid]}] "
            else:
                text = re.sub(r'<[^>]+>', '', token)
                para_str += text
        
        # Split by soft returns to maintain legacy line matching constraints
        for single_line in para_str.split('\n'):
            if single_line.strip():
                lines.append(single_line.strip())
            
    return lines

def parse_docx_file(file_path: str) -> list:
    questions = []
    
    # Extract flattened lines with images injected inline
    lines = extract_text_with_images(file_path)

    # Find where each question block begins (3 lines before the "(N)" question number)
    block_starts = []
    for i, line in enumerate(lines):
        if re.match(r'^\[IMAGE:\s*.*?\]\s*\(\d+\)|^\(\d+\)', line):
            start_idx = max(0, i - 3)
            block_starts.append(start_idx)

    # Reconstruct blocks
    for idx in range(len(block_starts)):
        start = block_starts[idx]
        end = block_starts[idx+1] if idx + 1 < len(block_starts) else len(lines)
        block_text = '\n'.join(lines[start:end])
        
        print(f"  Parsing block {idx + 1}...")
        q = parse_block(block_text)
        if q:
            questions.append(q)
        else:
            print(f"  [WARN] Block {idx + 1} could not be parsed — skipped.")

    return questions


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    os.makedirs("data", exist_ok=True)

    english_path = "data/english.docx"
    hindi_path = "data/hindi.docx"
    output_path = "data/parsed_questions.json"

    if not os.path.exists(english_path):
        print(f"[ERROR] English docx not found at: {english_path}")
        return

    print(f"\n📄 Parsing English questions from: {english_path}")
    en_questions = parse_docx_file(english_path)
    print(f"   ✅ Found {len(en_questions)} English questions.")

    hi_questions = []
    if os.path.exists(hindi_path):
        print(f"\n📄 Parsing Hindi questions from: {hindi_path}")
        hi_questions = parse_docx_file(hindi_path)
        print(f"   ✅ Found {len(hi_questions)} Hindi questions.")
    else:
        print(f"\n   ℹ️  No hindi.docx found — Hindi fields will be empty.")

    merged = merge_questions(en_questions, hi_questions)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(merged)} parsed questions → {output_path}")


if __name__ == "__main__":
    main()
