"""出题：AI 生成选择题"""
import json
from config.settings import CPD, RAW, DIFFS, get_subjects
from database.knowledge_point import kp_list
from ai.client import call_ai
from compile.frontmatter import list_compiled
from harvest.file_harvest import list_raw

def generate_quiz(subject, difficulty, count, course_id=None, weak_first=True, focus_kp_ids=None):
    knowledge_parts, page_names = [], []
    subjects_to_search = [subject] if subject else [s for s in get_subjects() if list_compiled(s)]
    for subj in subjects_to_search:
        for base_dir in [CPD, RAW]:
            folder = base_dir / subj
            if folder.exists():
                for f in folder.glob("*.md"):
                    content = f.read_text(encoding="utf-8")
                    knowledge_parts.append(f"## [{subj}] {f.stem}\n{content[:2000]}")
                    page_names.append(f"{subj}/{f.stem}")
        if knowledge_parts and subject:
            break  # 单学科找到内容即停；全科模式继续搜下一个学科
    if not knowledge_parts:
        available = [s for s in get_subjects() if list_compiled(s) or list_raw(s)]
        hint = f"可选学科：{', '.join(available)}" if available else "请先在「知识收割」页上传资料"
        return f"⚠️ 暂无可用资料。{hint}", None

    kp_rows = kp_list(course_id) if course_id else []
    # 专项突破：只保留选中的知识点
    if focus_kp_ids:
        focus_set = set(focus_kp_ids)
        kp_rows = [r for r in kp_rows if r[0] in focus_set]
    kp_map = {row[2]: row[0] for row in kp_rows}
    kp_list_str = "\n".join(
        f"ID={row[0]}, 名称={row[2]}, 掌握度={row[5]:.0%}" + ("（薄弱⚠️）" if row[8] else "")
        for row in kp_rows
    ) if kp_rows else "（暂无知识点数据）"

    weak_kps = [row[2] for row in kp_rows if row[8]] if weak_first else []
    diff_map = {"自动匹配": "基础30%+中等50%+困难20%", "基础": "全部基础", "中等": "全部中等", "困难": "全部困难"}
    diff_inst = diff_map.get(difficulty, "基础30%+中等50%+困难20%")
    weak_inst = f"优先针对以下薄弱知识点出题：{', '.join(weak_kps[:5])}" if weak_kps else ""

    prompt = f"""基于以下知识点列表和知识内容生成{count}道选择题(4选项A/B/C/D)。{diff_inst}。{weak_inst}
每道题必须包含 knowledge_point_id 字段（用知识点ID，不是名称）。返回严格JSON：
{{"questions":[{{"knowledge_point_id":1,"question":"题目","options":["A.xx","B.xx","C.xx","D.xx"],"answer":"A","explanation":"解析(100字内)","source_page":"页面名","difficulty":"基础/中等/困难"}}]}}

知识点列表（出题时用 knowledge_point_id 关联）：
{kp_list_str}

可用页面：{', '.join(page_names)}

知识内容：\n{''.join(knowledge_parts)[:8000]}"""

    r = call_ai(prompt, json_mode=True, temperature=0.9)
    try:
        questions = json.loads(r).get("questions", [])
        for q in questions:
            if not q.get("knowledge_point_id"):
                src = q.get("source_page", "")
                for name, kid in kp_map.items():
                    if name in src or src in name:
                        q["knowledge_point_id"] = kid
                        break
        return questions, page_names
    except:
        return f"⚠️ 题目解析失败：{r[:200]}", None
