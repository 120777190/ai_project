# src/core/llm/thinker.py
# ====== 思考者模块 ======
# 职责：思考者函数 ask_ai_with_context()

import requests
from src.config.settings import settings


def ask_ai_with_context(question, all_contents, extra_prompt=""):
    """基于多个文档内容回答问题，可接受额外提示词"""
    combined = ""
    for doc in all_contents:
        combined += f"\n\n【文档：{doc['name']}】\n{doc['content']}"

    system_prompt = f"""请基于以下多个文档的内容回答用户的问题。

注意事项：
1. 如果多个文档中有相关信息，可以综合引用。
2. 如果文档中的信息与用户问题在时间、人物、事件主体上存在不一致，请先指出这种不一致。
3. 如果所有文档中都没有相关信息，请说"文档中没有提到这个问题"。
4. 不要编造信息。

=== 所有文档内容 ===
{combined}
=== 文档内容结束 ===
"""
    if extra_prompt.strip():
        system_prompt += f"\n\n{extra_prompt}"

    headers = {
        "Authorization": f"Bearer {settings.API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": settings.DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户问题：{question}\n回答："}
        ],
        "stream": False
    }
    url = f"{settings.BASE_URL}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=data, timeout=settings.API_TIMEOUT)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"请求出错：{e}"