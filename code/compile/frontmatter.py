"""Frontmatter 解析 + 文件列表"""
import re
from config.settings import CPD, get_subjects

def parse_fm(content):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if m:
        fm = {}
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
        return fm, m.group(2)
    return {}, content

def list_compiled(subject=None):
    dirs = [CPD / subject] if subject else [CPD / s for s in get_subjects()]
    files = []
    for d in dirs:
        if d.exists():
            files.extend(d.glob("*.md"))
    return files
