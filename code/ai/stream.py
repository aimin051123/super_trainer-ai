"""SSE 流式显示"""
import streamlit as st
from ai.client import call_ai

def stream_display(prompt, system_prompt=None):
    placeholder = st.empty()
    full_text = ""
    buffer = []
    for token in call_ai(prompt, system_prompt, stream=True):
        if isinstance(token, str) and token.startswith("⚠️"):
            placeholder.error(token)
            return token
        buffer.append(token)
        full_text += token
        if len(buffer) >= 3 or token in "，。！？\n":
            placeholder.markdown(full_text + "▌")
            buffer = []
    placeholder.markdown(full_text)
    return full_text
