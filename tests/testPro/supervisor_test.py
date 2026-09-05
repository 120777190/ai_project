import requests
import json

API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"
URL = "https://api.deepseek.com/v1/chat/completions"

SUPERVISOR_PROMPT = """你是一个推理监督者。你的任务是分析思考者的输出，判断其是否陷入了“纵向死胡同”。

判断标准（满足任意一条即触发警报）：
1. 连续多次尝试同一方向的修复，且每次改动幅度小、方向单一
2. 反复评估同一选项的利弊，没有引入新的变量或替代方案
3. 同一主题下，多次输出的结构和表达高度相似，核心逻辑未变
4. 在多步骤推理中，反复推导同一卡点，没有尝试跳过或换方向

输入：思考者的最新输出内容。

输出格式（严格按以下JSON格式）：
{"triggered": true/false, "matched_rules": [], "reason": "说明原因", "intervention": "引导指令"}
"""

def supervise(thinking_output):
    """监督者：判断思考者是否陷入死胡同"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": thinking_output}
    ]
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": False,
        "temperature": 0.1  # 低温度，让输出更稳定
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # 尝试解析JSON
        return json.loads(content)
    except Exception as e:
        return {
            "triggered": False,
            "error": str(e),
            "reason": "监督者调用失败",
            "intervention": ""
        }

# 测试用例
if __name__ == "__main__":
    # 模拟思考者陷入死胡同的输出
    test_output = """
    看起来还是编码的问题，我建议再试一下改成UTF-8编码。
    不行的话试试GBK，或者试试Latin-1，应该能解决。
    我觉得编码问题就是根本原因，改一下应该就好了。
    """
    
    result = supervise(test_output)
    print(json.dumps(result, ensure_ascii=False, indent=2))