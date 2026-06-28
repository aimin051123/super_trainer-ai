"""知识检索：关键词匹配"""
from config.settings import CPD, get_subjects

def search_knowledge(query, top_k=5):
    qwords = set(query)
    scored = []
    for s in get_subjects():
        d = CPD / s
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            score = sum(content.count(w) for w in qwords)
            if any(w in f.stem for w in qwords):
                score += 10
            if score > 0:
                scored.append((f.stem, s, content, score))
    scored.sort(key=lambda x: -x[3])
    return scored[:top_k]
