import re

xml = open("doc_xml.txt", encoding="utf-8").read()
tags = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
with open("tags.txt", "w", encoding="utf-8") as f:
    for t in tags[:200]:
        f.write(t + "\n")
