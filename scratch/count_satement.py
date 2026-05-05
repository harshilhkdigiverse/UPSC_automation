"""Count all 'Satement' occurrences in the lines extracted from english.docx"""
import docx, re, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_runs_text(element):
    from docx.text.run import Run
    text = ""
    for r_node in element.xpath('.//w:r'):
        run = Run(r_node, None)
        if run.text: text += run.text
    return text

def iter_block_items(parent):
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    parent_elm = parent.element.body if isinstance(parent, docx.document.Document) else parent._element
    for child in parent_elm.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P): yield Paragraph(child, parent)
        elif isinstance(child, docx.oxml.table.CT_Tbl): yield Table(child, parent)

doc = docx.Document(r'd:\UPSC_automation\data\english.docx')
lines = []
for item in iter_block_items(doc):
    from docx.text.paragraph import Paragraph
    if isinstance(item, Paragraph):
        p_text = get_runs_text(item._element)
        for sl in p_text.split('\n'):
            if sl.strip(): lines.append(sl.strip())
    else:
        for row in item.rows:
            row_text = [get_runs_text(cell._element).strip() for cell in row.cells]
            row_text = [t for t in row_text if t]
            if len(row_text) > 1: lines.append("=".join(row_text))
            elif len(row_text) == 1: lines.append(row_text[0])

satement_lines = [(i, l) for i, l in enumerate(lines) if l.lower().strip() in {'satement', 'satement '}]
print(f"Lines matching 'Satement' exactly: {len(satement_lines)}")
for i, l in satement_lines:
    print(f"  [{i}] prev={lines[i-1]!r} | curr={l!r} | next={lines[i+1]!r}")

# Also check what is right after 'Satement' in word context
print("\nAll lines containing 'satement' (case-insensitive):")
for i, l in enumerate(lines):
    if 'satement' in l.lower():
        print(f"  [{i}] {l[:100]!r}")
