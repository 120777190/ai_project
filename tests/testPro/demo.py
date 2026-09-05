import requests
import json

API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"
URL = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": "用一句话解释什么是RAG"}
    ],
    "stream": False
}

try:
    response = requests.post(URL, headers=headers, json=data, timeout=30)
    print("状态码：", response.status_code)
    print("完整响应：", response.text)  # 打印全部返回内容
except Exception as e:
    print("请求出错：", e)