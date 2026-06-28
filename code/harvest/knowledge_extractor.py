"""AI 知识点提取"""
import json
from ai.client import call_ai
from database.knowledge_point import kp_upsert

def extract_knowledge_points(course_id, text):
    prompt = f"""从以下文本中提取所有结构化知识点。返回严格JSON：
{{"knowledge_points":[{{"name":"知识点名称","description":"一句话描述","importance":"high/medium/low"}}]}}

文本：{text[:4000]}"""
    r = call_ai(prompt, json_mode=True, temperature=0.3)
    try:
        data = json.loads(r)
        count = 0
        for kp in data.get("knowledge_points", []):
            kp_upsert(course_id, kp.get("name",""), kp.get("description",""), kp.get("importance","medium"))
            count += 1
        return count
    except:
        return 0
