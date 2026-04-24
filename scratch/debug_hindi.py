# -*- coding: utf-8 -*-
import docx
import sys
import io

# Force UTF-8 output
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

# Print first 80 lines
for i, l in enumerate(lines[:80]):
    print(f'{i:3d}: {l}')
