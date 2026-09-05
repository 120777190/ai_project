# src/core/llm/supervisor.py
# ====== 监督者模块 ======
# 职责：监督者 Prompt + supervise() 函数

import requests
import json

from src.config.settings import settings


# ====== 监督者Prompt ======
SUPERVISOR_PROMPT = """你是一个推理监督者。你的任务是分析思考者与用户之间的对话，判断思考者是否陷入了"纵向死胡同"或"交互无效循环"或"虚构推理产生幻觉结论"。

判断标准（满足任意一条即触发警报）：
1. 连续多次尝试同一方向的修复，且每次改动幅度小、方向单一
2. 反复评估同一选项的利弊，没有引入新的变量或替代方案
3. 同一主题下，多次输出的结构和表达高度相似，核心逻辑未变
4. 在多步骤推理中，反复推导同一卡点，没有尝试跳过或换方向
5. 用户发送的内容中包含重复的信息（如反复提问相同问题、反复强调同一个现象）
6. 用户表达了对当前方向的否定态度（如"还是不对""不是这个问题""方向错了"等）
7. 思考者输出的任何结论，如果是基于惯性、直觉或常见假设得出的，必须要求其返回文档原文或数据来源作为事实依据进行可靠性确认。若结论无法追溯到具体来源，视为不可靠。
8. 如果思考者确实无法从上下文中找到直接事实依据，允许其基于理论进行推论，但必须：① 明确标注"此为推论，非事实"② 以提示方式告知用户"当前结论基于理论推导，请提供相关事实依据以佐证"③ 推论与已知事实矛盾时，必须优先说明矛盾点。

触发警报后的处理方式（按优先级排序）：
1. 横向思考（优先）：跳出当前局限，检索整个对话历史，找出所有被忽略的方向和线索，一一罗列
2. 纵向思考（次选）：沿着当前方向深入挖掘，追问"这个问题的根源是什么"，而非停留在表面
3. 外部信息检索（备选）：引导思考者向用户提出需要补充的信息，或通过联网搜索获取外部数据
4. 事实核查：如果怀疑思考者基于惯性得出结论，强制要求其提供文档原文或数据来源
5. 透明推理（新增）：如果确实无事实依据，允许推论，但必须明确告知用户这是推论，并请求提供佐证

输入：当前轮次的对话内容（用户输入 + 思考者输出），以及历史对话摘要（如有）。

输出格式（严格按以下JSON格式）：
{
  "triggered": true/false,
  "matched_rules": [],
  "reason": "简要说明触发原因",
  "intervention": {
    "direction": "lateral",
    "instruction": "具体的引导指令",
    "priority": 1
  }
}
"""


def supervise(user_question, thinker_response):
    """监督者：判断思考者是否陷入死胡同，并返回干预指令"""
    headers = {
        "Authorization": f"Bearer {settings.API_KEY}",
        "Content-Type": "application/json"
    }
    input_text = f"用户问题：{user_question}\n思考者回答：{thinker_response}"
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": input_text}
    ]
    data = {
        "model": settings.DEFAULT_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0.1
    }
    url = f"{settings.BASE_URL}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=data, timeout=settings.SUPERVISOR_TIMEOUT)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        # 数据清洗：确保字段结构完整
        if not isinstance(parsed, dict):
            parsed = {}
        if "intervention" not in parsed or parsed["intervention"] is None:
            parsed["intervention"] = {}
        if "triggered" not in parsed:
            parsed["triggered"] = False

        return parsed

    except Exception as e:
        return {
            "triggered": False,
            "error": str(e),
            "reason": "监督者调用失败",
            "intervention": {}
        }