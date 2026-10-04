import math
import re

print("1. 加载文档...")
# 为了模拟真实的文档读取，我们直接在代码里写一段长文本
# 以后你只需把这里换成 PdfReader 读取本地 PDF 的代码即可
raw_document = """
软件测试是为了发现错误而执行程序的过程。它不仅仅是为了证明程序是对的，更是为了找出隐藏的错误。
Python是一门简洁且功能强大的编程语言，在人工智能领域有着广泛的应用。
今天深圳的天气很热，晒伤之后要多喝水，避免长时间暴露在阳光下。
RAG技术结合了检索和生成，它通过外部知识库来增强大模型的回答准确性。
"""

print("2. 文档切块（Chunking）...")
# 按句号切分成小块（这就是最简单的切块策略）
chunks = [chunk.strip() for chunk in raw_document.split("。") if chunk.strip()]
print(f"   切分完成，共 {len(chunks)} 块")

print("3. 向量化（用简单的Hash模拟，不需要API）...")
# 重点：我们用一个简单的哈希函数把文本变成"伪向量"，模拟Embedding的过程
# 这样不用连外网，不用装库，纯Python跑通流程！
def simple_hash_embedding(text, dim=10):
    # 生成10维向量，每一维是这个文本的哈希特征
    vector = [0.0] * dim
    for i, char in enumerate(text):
        vector[i % dim] += ord(char) * 0.01
    # 归一化（除以长度）
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    return vector

# 给每个块算向量
chunk_embeddings = [simple_hash_embedding(chunk) for chunk in chunks]
print("   向量化完成")

print("4. 开始检索...")
# 模拟用户提问
question = "我晒伤了应该怎么办？"
print(f"   用户提问：{question}")

# 给提问算向量
query_embedding = simple_hash_embedding(question)

# 手写余弦相似度（就是咱们下午跑通的那个）
def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0
    return dot_product / (mag1 * mag2)

# 计算每一块的相似度
scores = []
for i, chunk_vec in enumerate(chunk_embeddings):
    score = cosine_similarity(query_embedding, chunk_vec)
    scores.append((score, chunks[i]))

# 按相似度排序，取前1个
scores.sort(key=lambda x: x[0], reverse=True)

print("\n5. 最终检索结果（最匹配的文档片段）：")
print(f"【{scores[0][1]}】")
print(f"  相似度得分：{scores[0][0]:.4f}")