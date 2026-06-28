"""学科分类：AI 优先 + 关键词回退"""
import json
from config.settings import RAW, CPD, KW_DICT, get_subjects
from ai.client import call_ai

def classify_subject(text):
    existing = "、".join(get_subjects())
    r = call_ai(f"判断以下文本属于哪个学科。已知学科：{existing}；如果都不匹配，返回一个新学科名。只返回JSON：{{\"subject\":\"学科名\"}}\n\n{text[:3000]}",
                json_mode=True, temperature=0.3)
    try:
        s = json.loads(r).get("subject", "").strip()
        if s:
            for parent in [RAW, CPD]:
                (parent / s).mkdir(parents=True, exist_ok=True)
            return s
    except:
        pass
    scores = {s: sum(1 for k in ks if k in text) for s, ks in KW_DICT.items()}
    best = max(scores, key=scores.get) if any(scores.values()) else None
    return best if best and scores[best] > 0 else "其他学科"

def classify_entity(text):
    r = call_ai(f"判断以下笔记的类型（概念/算法/对比/考试技巧）并给出20字以内标题，返回JSON：{{\"type\":\"类型\",\"title\":\"标题\"}}\n\n{text[:2000]}",
                json_mode=True, temperature=0.3)
    try:
        d = json.loads(r)
        return d.get("type", "概念"), d.get("title", "学习笔记")
    except:
        if any(kw in text for kw in ["区别","对比","vs","不同于"]): return "对比", "概念对比"
        if any(kw in text for kw in ["步骤","流程","伪代码","算法"]): return "算法", "算法笔记"
        if any(kw in text for kw in ["技巧","记住","口诀","考点","易错"]): return "考试技巧", "考试技巧"
        return "概念", "概念理解"
