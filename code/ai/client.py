"""DeepSeek API 调用"""
import httpx
from openai import OpenAI
from config.settings import BASE_URL, MODEL, TIMEOUT, _config, get_api_key

def call_ai(prompt, system_prompt=None, json_mode=False, stream=False, temperature=0.7):
    key = get_api_key()
    if not key:
        return "⚠️ 请先设置 DEEPSEEK_API_KEY（创建 config.properties 或设置环境变量）"
    proxy_url = _config.get("DEFAULT", "DEEPSEEK_PROXY", fallback="http://127.0.0.1:7897")
    http_client = httpx.Client(proxy=proxy_url, timeout=TIMEOUT)
    client = OpenAI(api_key=key, base_url=BASE_URL, http_client=http_client)
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": prompt})
    kwargs = {"model": MODEL, "messages": msgs, "temperature": temperature, "max_tokens": 4096, "timeout": TIMEOUT}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if stream:
        kwargs["stream"] = True
    try:
        response = client.chat.completions.create(**kwargs)
        if stream:
            return (chunk.choices[0].delta.content or "" for chunk in response)
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI调用失败：{e}"
