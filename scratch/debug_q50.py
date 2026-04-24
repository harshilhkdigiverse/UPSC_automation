# -*- coding: utf-8 -*-
import docx
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx.text.paragraph import Paragraph
from docx.table import Table

doc = docx.Document('data/hindi.docx')
img_map = {r_id: rel.target_part for r_id, rel in doc.part.rels.items() if 'image' in rel.reltype}

def iter_block_items(parent):
    if isinstance(parent, docx.document.Document):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._element
    for child in parent_elm.iterchildren():
        if isinstance(child, docx.oxml.text.paragraph.CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, docx.oxml.table.CT_Tbl):
            yield Table(child, parent)

lines = []
for item in iter_block_items(doc):
    if isinstance(item, Paragraph):
        p_text = ''
        for run in item.runs:
            p_text += run.text
        for sl in p_text.split('\n'):
            if sl.strip():
                lines.append(sl.strip())
    else:
        for row in item.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if len(row_text) > 1:
                lines.append('='.join(row_text))
            elif len(row_text) == 1:
                lines.append(row_text[0])

# Find Q50 area
for i, l in enumerate(lines):
    if re.search(r'\b50\b', l) and i > 0:
        print(f'Line {i}: {l}')
        if i > 3:
            print(f'  Context (-3): {lines[i-3]}')
            print(f'  Context (-2): {lines[i-2]}')
            print(f'  Context (-1): {lines[i-1]}')
        for j in range(i, min(i+15, len(lines))):
            print(f'  {j}: {lines[j]}')
        break

print('\n--- Last 20 lines ---')
for i, l in enumerate(lines[-20:]):
    print(f'{len(lines)-20+i}: {l}')
