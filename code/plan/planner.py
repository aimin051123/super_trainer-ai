"""复习规划：艾宾浩斯遗忘曲线 + AI 生成"""
from datetime import datetime
from config.settings import CPD, get_subjects
from database.connection import db_query
from database.knowledge_point import kp_list, kp_get_weak, kp_get_observing
from ai.client import call_ai

def generate_plan(course_id, daily_minutes, custom_req="", exam_dates=None):
    if not exam_dates: exam_dates = {}
    earliest = None
    date_lines = []
    for s, d in exam_dates.items():
        days = (d - datetime.now().date()).days
        date_lines.append(f"- {s}：{d}（剩余 {days} 天）")
        if earliest is None or d < earliest: earliest = d

    if not date_lines:
        return "⚠️ 请先设置考试日期"

    kp_rows = kp_list(course_id)
    weak_rows = kp_get_weak(course_id)
    weak_str = "\n".join(
        f"- {row[2]}（正确率{row[5]:.0%}，{row[9]}）"
        for row in weak_rows
    ) if weak_rows else "（暂无薄弱点）"

    stats = []
    for s in get_subjects():
        d = CPD / s
        pc = len(list(d.glob("*.md"))) if d.exists() else 0
        stats.append(f"- {s}：{pc}个知识页面")
    for row in kp_rows:
        found = False
        for i, st in enumerate(stats):
            if row[2] in st: found = True; break
        if not found:
            stats.append(f"- {row[2]}：掌握度{row[5]:.0%}" + ("⚠️薄弱" if row[8] else ""))

    prompt = f"""制定期末复习计划。遵循以下规则：

1. 艾宾浩斯遗忘曲线：每个知识点首次学习后，在第 1、2、4、7、15 天后需安排复习
2. 薄弱点（正确率<60%）优先安排在前期
3. 每天不超过 {daily_minutes} 分钟
4. 每天不超过 2 个学科，避免频繁切换
5. 最后 3 天安排总复习 + 所有错题回顾

{"6. 学生自定义要求（必须遵守）：" + custom_req if custom_req else ""}

各科考试日期：
{chr(10).join(date_lines)}
每日可用时长：{daily_minutes} 分钟

学科统计：
{chr(10).join(stats)}

薄弱点（优先安排）：
{weak_str}

按日期列出每日任务（学科 + 知识点 + 预计用时 + 是否做题）。用 Markdown 表格格式。"""

    return call_ai(prompt)

def detect_weak_points(course_id):
    weak = [{"page": r[2], "subject": r[1], "accuracy": r[5], "total": r[6], "reason": r[9]}
            for r in kp_get_weak(course_id)]
    obs = [{"page": r[2], "subject": r[1], "accuracy": r[5], "total": r[6], "reason": r[9]}
           for r in kp_get_observing(course_id)]
    return weak, obs
