import requests
import math
import os
import json

from pypdf import PdfReader


# 1. 配置智谱 API 信息
API_KEY = "3cf128c0e68e486d840e99cc89312ea4.PEZ4km6risIosXE2"
URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"

SPEAK_API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"
SPEAK_URL = "https://api.deepseek.com/chat/completions"

def get_embedding(texts):
    """调用智谱 API，把文本变成真实的 2048 维向量"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "embedding-3",  # 智谱最新的 Embedding 模型
        "input": texts
    }
    response = requests.post(URL, headers=headers, json=data)
    
    if response.status_code == 200:
        # 提取返回的向量
        #return response.json()["data"][0]["embedding"]
        datas = response.json()["data"]
        embeddings = []
        for i in datas:
            embedding = i["embedding"]  
            embeddings.append(embedding)
        return embeddings
    else:
        print("❌ 智谱API 请求失败：", response.text)
        return None

def get_answer(query,reference_data):
    """让语言模型根据匹配到的資料来回答用户的问题"""
    headers = {
        "Authorization": f"Bearer {SPEAK_API_KEY}",
        "Content-Type": "application/json"
    }
    chat_data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手。请严格根据提供的资料回答用户问题，不要自己编造。"},
            {"role": "user", "content": f"资料：{reference_data[0][1]}\n\n用户问题：{query}"}
        ]
    }
    response = requests.post(SPEAK_URL, headers=headers, json=chat_data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("❌ 小鲸鱼API 请求失败：", response.text)
        return None

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0

#获取pdf前三页测试
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    # 只读前3页
    for page in reader.pages[:3]:
        text += page.extract_text()
    return text

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    text_length = len(text)
    
    # 循环直到指针走到文本末尾
    while start < text_length:
        # 1. 计算这一块的结束位置（不能超过总长度）
        end = start + chunk_size
        if end > text_length:
            end = text_length
            
        # 2. 切片并存入 chunks 列表
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 3. 关键：更新 start 指针。
        # 正常应该是 start += chunk_size，但因为有重叠，必须减去 overlap
        start += (chunk_size - overlap)
        
        # 4. 防御机制：如果已经切到末尾，就退出循环
        if end == text_length:
            break
            
    return chunks

# 2. 准备测试文本（注意第三句，我们故意把“晒伤”写成“太阳烤红了”）
documents = [
    "软件测试是为了发现错误而执行程序的过程。",
    "Python是一门简洁且功能强大的编程语言。",
    "今天深圳的天气很热，太阳烤红了皮肤，要多喝水。"
]

documents = chunk_text(read_pdf("G:\\书架\\硅谷禁书\\硅谷禁书.pdf"))
batch_size = 10
all_embeddings = []

for i in range(0,len(documents),batch_size):
    batch = documents[i:i+batch_size]
    batch_embeddings = get_embedding(batch)
    all_embeddings.extend(batch_embeddings)

# 3. 把文档变成真实的向量
print("正在调用智谱 API 计算真实向量，请稍候...")
#doc_embeddings = [get_embedding(doc) for doc in documents]
#doc_embeddings = get_embedding(documents)

if all(all_embeddings):
    # 4. 模拟用户提问（故意不用“晒伤”字眼）
    query = "如何改变自己获得成功"
    print(f"\n用户提问：{query}")
    query_vec = get_embedding(query)[0]

    print("all_embeddings 的长度是：", len(all_embeddings))
    print("all_embeddings[0] 的长度是：", len(all_embeddings[0]))

    # 5. 计算相似度并排序
    scores = []
    for i, doc_vec in enumerate(all_embeddings):
        score = cosine_similarity(query_vec, doc_vec)
        scores.append((score, documents[i]))

    scores.sort(key=lambda x: x[0], reverse=True)
    print("\n✅ 真实语义检索结果（最匹配的 Top 1）：")
    print(f"【{scores[0][1]}】")
    print(f"相似度得分：{scores[0][0]:.4f}")
    answer = get_answer(query,scores)
    print("小鲸鱼：",answer)
