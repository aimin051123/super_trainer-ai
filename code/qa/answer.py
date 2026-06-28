"""知识问答：多轮对话 + SSE 流式"""
import streamlit as st
from ai.stream import stream_display
from database.chat_history import chat_save, chat_recent
from qa.retriever import search_knowledge

def answer_question(question, course_id=None):
    hits = search_knowledge(question)
    if not hits:
        return "⚠️ 知识库中没有找到相关内容，请先上传资料并编译知识", []

    ctx = "\n\n---\n\n".join(f"【来源：{n}({s})】\n{c[:1500]}" for n, s, c, _ in hits)
    sources = [f"[[{n}]]（{s}）" for n, s, _, _ in hits]
    system_prompt = f"你是学习助手 SuperTutor。请基于以下资料回答学生问题。如资料不足请诚实告知，不要编造。\n\n参考资料：\n{ctx[:6000]}"

    if course_id:
        history = chat_recent(course_id, 10)
        history_text = "\n".join(f"[{r}]: {c[:200]}" for r, c in history)
        system_prompt += f"\n\n对话历史：\n{history_text}"

    full_text = stream_display(question, system_prompt)

    if course_id:
        chat_save(course_id, "user", question)
        chat_save(course_id, "assistant", full_text)

    return full_text, sources
