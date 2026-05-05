
import docx
import re
import os

def get_runs_text(element):
    from docx.text.run import Run
    text = ""
    for r_node in element.xpath('.//w:r'):
        run = Run(r_node, None)
        if run.text:
            text += run.text
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

def debug_docx(path):
    print(f"--- Fulfilling debug for {path} ---")
    doc = docx.Document(path)
    lines = []
    for item in iter_block_items(doc):
        from docx.text.paragraph import Paragraph
        if isinstance(item, Paragraph):
            p_text = get_runs_text(item._element)
            if item._element.xpath('.//w:numPr'):
                p_text = f"(1) {p_text}"
            for sl in p_text.split('\n'):
                if sl.strip(): lines.append(sl.strip())
    
    for i, line in enumerate(lines[:100]):
        print(f"{i}: {line}")

if __name__ == '__main__':
    debug_docx('data/english.docx')
