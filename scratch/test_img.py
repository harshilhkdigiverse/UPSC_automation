import docx
import os
import re

def test_extract():
    if not os.path.exists('data/english.docx'):
        print("data/english.docx not found")
        return
    doc = docx.Document('data/english.docx')
    os.makedirs('data/images', exist_ok=True)
    
    img_map = {}
    for r_id, rel in doc.part.rels.items():
        if 'image' in rel.reltype:
            img_map[r_id] = rel.target_part

    for p in doc.paragraphs:
        line_text = ''
        for run in p.runs:
            line_text += run.text
            # Use xml to find drawing
            xml = run._element.xml
            if '<w:drawing>' in xml:
                # Find rIdx
                m = re.search(r'r:embed=\"(rId\d+)\"', xml)
                if m:
                    rid = m.group(1)
                    if rid in img_map:
                        img_part = img_map[rid]
                        fname = img_part.partname.split('/')[-1]
                        # Save the image if it doesn't exist
                        out_path = os.path.join('data/images', fname)
                        with open(out_path, 'wb') as f:
                            f.write(img_part.blob)
                        abs_path = os.path.abspath(out_path).replace("\\", "/")
                        line_text += f' [IMAGE: {abs_path}] '
        if line_text.strip():
            print(f'PARA: {line_text.strip()}')

if __name__ == "__main__":
    test_extract()
