
import docx
import re

def find_images_xml(path):
    doc = docx.Document(path)
    # Check paragraphs, tables, sections
    # Sections have headers/footers
    items = []
    # Body
    if '<w:drawing>' in doc.element.body.xml or '<w:pict>' in doc.element.body.xml:
        print("Images found in BODY.")
    
    # Headers/Footers
    for section in doc.sections:
        if section.header and ('<w:drawing>' in section.header._element.xml or '<w:pict>' in section.header._element.xml):
            print("Images found in HEADER.")
        if section.footer and ('<w:drawing>' in section.footer._element.xml or '<w:pict>' in section.footer._element.xml):
            print("Images found in FOOTER.")

if __name__ == '__main__':
    find_images_xml('data/english.docx')
