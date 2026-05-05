import docx
import os

def dump_text(file_path):
    doc = docx.Document(file_path)
    text = []
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    
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

    for item in iter_block_items(doc):
        if isinstance(item, Paragraph):
            text.append(item.text)
        elif isinstance(item, Table):
            for row in item.rows:
                text.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(text)

en_text = dump_text(r'd:\UPSC_automation\data\english.docx')
hi_text = dump_text(r'd:\UPSC_automation\data\hindi.docx')

with open(r'd:\UPSC_automation\scratch\en_dump.txt', 'w', encoding='utf-8') as f:
    f.write(en_text)

with open(r'd:\UPSC_automation\scratch\hi_dump.txt', 'w', encoding='utf-8') as f:
    f.write(hi_text)

print("Dumps created")
