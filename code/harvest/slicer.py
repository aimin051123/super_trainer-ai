"""文本切片：按标题行切分"""
import re

def slice_text(text):
    lines, sections, cur_title, cur_lines = text.split("\n"), [], "引言", []
    hd = re.compile(r"^(#{1,4}\s+.+|\d+[\.\、\)]\s*.+|第[一二三四五六七八九十\d]+[章节].+)")
    for line in lines:
        s = line.strip()
        if hd.match(s) and len(s) < 80:
            if cur_lines:
                sections.append((cur_title, "\n".join(cur_lines).strip()))
            cur_title, cur_lines = s.lstrip("#").strip(), []
        else:
            cur_lines.append(line)
    if cur_lines:
        sections.append((cur_title, "\n".join(cur_lines).strip()))
    if len(sections) <= 1 and len(text) > 500:
        sections = [(f"片段{i+1}", p.strip()) for i, p in enumerate(text.split("\n\n")) if p.strip()]
    return sections
