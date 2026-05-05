"""
Diagnose the specific issues:
1. Q61 - English block missing question text
2. Q62/63 - subtopic showing Unknown
3. Q75/84/97 - Hindi solution missing
"""
import docx, re, sys
sys.stdout.reconfigure(encoding='utf-8')

IMG_START = "[[IMG_START]]"
IMG_END = "[[IMG_END]]"

def get_runs_text(element):
    from docx.text.run import Run
    text = ""
    for r_node in element.xpath('.//w:r'):
        run = Run(r_node, None)
        if run.text:
            text += run.text
        xml = run._element.xml
        if '<w:drawing>' in xml:
            text += f" {IMG_START}img{IMG_END} "
    return text

def iter_block_items(parent):
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    if isinstance(parent, docx.document.Document):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._element
    for child in parent_elm.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            yield Table(child, parent)

def get_lines(file_path):
    doc = docx.Document(file_path)
    lines = []
    for item in iter_block_items(doc):
        from docx.text.paragraph import Paragraph
        if isinstance(item, Paragraph):
            p_text = get_runs_text(item._element)
            has_numpr = bool(item._element.xpath('.//w:numPr'))
            for sl in p_text.split('\n'):
                if sl.strip():
                    lines.append((sl.strip(), has_numpr))
        else:
            for row in item.rows:
                row_text = [get_runs_text(cell._element).strip() for cell in row.cells]
                row_text = [t for t in row_text if t]
                if len(row_text) > 1:
                    lines.append(("=".join(row_text), False))
                elif len(row_text) == 1:
                    lines.append((row_text[0], False))
    return lines

print("=" * 70)
print("ENGLISH DOC - Around Q61 (looking for line with '61')")
print("=" * 70)
en_lines = get_lines(r'd:\UPSC_automation\data\english.docx')
for i, (line, numpr) in enumerate(en_lines):
    if re.search(r'\b61\b', line):
        start = max(0, i-3)
        end = min(len(en_lines), i+20)
        print(f"\n>>> Found '61' at line {i}. Showing lines {start}-{end}:")
        for j in range(start, end):
            txt, np = en_lines[j]
            print(f"  [{j}] numPr={np} | {txt[:120]}")
        break

print("\n" + "=" * 70)
print("ENGLISH DOC - Q61 block header area (look for 'Art And Culture' near 61)")
print("=" * 70)
# Show lines 0..50 to see how blocks start
for i, (line, numpr) in enumerate(en_lines[:60]):
    print(f"  [{i}] numPr={numpr} | {line[:120]}")

print("\n" + "=" * 70)
print("HINDI DOC - Around Q75 solution (warning: Answer line missing)")
print("=" * 70)
hi_lines = get_lines(r'd:\UPSC_automation\data\hindi.docx')
for i, (line, numpr) in enumerate(hi_lines):
    if re.search(r'\b75\b', line):
        start = max(0, i-2)
        end = min(len(hi_lines), i+40)
        print(f"\n>>> Found '75' at line {i}. Showing lines {start}-{end}:")
        for j in range(start, end):
            txt, np = hi_lines[j]
            print(f"  [{j}] numPr={np} | {txt[:120]}")
        break

print("\n" + "=" * 70)
print("HINDI DOC - Around Q84")
print("=" * 70)
for i, (line, numpr) in enumerate(hi_lines):
    if re.search(r'\b84\b', line):
        start = max(0, i-2)
        end = min(len(hi_lines), i+40)
        print(f"\n>>> Found '84' at line {i}. Showing lines {start}-{end}:")
        for j in range(start, end):
            txt, np = hi_lines[j]
            print(f"  [{j}] numPr={np} | {txt[:120]}")
        break

print("\n" + "=" * 70)
print("HINDI DOC - Around Q97")
print("=" * 70)
for i, (line, numpr) in enumerate(hi_lines):
    if re.search(r'\b97\b', line):
        start = max(0, i-2)
        end = min(len(hi_lines), i+50)
        print(f"\n>>> Found '97' at line {i}. Showing lines {start}-{end}:")
        for j in range(start, end):
            txt, np = hi_lines[j]
            print(f"  [{j}] numPr={np} | {txt[:120]}")
        break
