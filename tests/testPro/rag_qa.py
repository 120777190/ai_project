import requests
import json
import os
from src.utils.read_doc import read_file  # 复用上一步的文档读取功能

# ====== 配置 ======
API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"  # 替换成你的真实API Key
URL = "https://api.deepseek.com/v1/chat/completions"

def ask_ai_with_context(user_question, document_content):
    """
    基于文档内容回答问题
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建提示词：让AI基于文档内容回答
    system_prompt = f"""你是一个基于文档回答问题的助手。
请严格基于以下文档内容回答用户的问题。
如果文档中没有相关信息，请直接说"文档中没有提到这个问题"，不要编造答案。

=== 文档内容 ===
{document_content}
=== 文档内容结束 ===
"""
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"请求出错：{e}"

# ====== 主程序 ======
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 RAG 知识库问答系统")
    print("=" * 60)
    
    # 1. 输入文档路径
    doc_path = input("📂 请输入文档路径（支持 .txt / .pdf / .docx）：").strip()
    
    if not os.path.exists(doc_path):
        print("❌ 文件不存在，请检查路径")
        exit()
    
    # 2. 读取文档
    print("📄 正在读取文档...")
    doc_content = read_file(doc_path)
    
    if "出错" in doc_content or "不支持" in doc_content:
        print(f"❌ 读取失败：{doc_content}")
        exit()
    
    print(f"✅ 文档读取成功，共 {len(doc_content)} 个字符")
    print("-" * 60)
    
    # 3. 问答循环
    print("💬 可以开始提问了（输入 'exit' 退出）")
    while True:
        question = input("\n❓ 你的问题：").strip()
        if question.lower() in ['exit', 'quit', '退出']:
            print("👋 再见！")
            break
        if not question:
            continue
        
        print("⏳ AI 正在思考...")
        answer = ask_ai_with_context(question, doc_content)
        print(f"\n🤖 回答：\n{answer}")
        print("-" * 60)