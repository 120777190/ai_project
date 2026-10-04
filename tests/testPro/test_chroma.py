import math

print("1. 纯Python内存检索启动")

# 模拟3篇文档和它们对应的向量（现实中向量是模型算的，这里我们手写3个假向量）
documents = [
    "软件测试是为了发现错误而执行程序的过程。",
    "Python是一门简洁且功能强大的编程语言。",
    "今天深圳的天气很热，晒伤之后要多喝水。"
]

# 对应上面三篇文档的向量（每个向量3个数字）
doc_embeddings = [
    [0.1, 0.2, 0.3],
    [0.9, 0.8, 0.7],
    [0.4, 0.5, 0.6]
]

# 模拟用户提问的向量
query_embedding = [0.9, 0.8, 0.7]
print("2. 向量准备就绪")

# 手写一个余弦相似度计算函数（这是向量检索的核心算法）
def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

# 计算提问和每篇文档的相似度
scores = []
for i, doc_vec in enumerate(doc_embeddings):
    score = cosine_similarity(query_embedding, doc_vec)
    scores.append((score, documents[i]))

print("3. 相似度计算完成")

# 按相似度从高到低排序
scores.sort(key=lambda x: x[0], reverse=True)

print("4. 检索结果（最匹配的前1条）：")
print(f"【{scores[0][1]}】 (相似度得分: {scores[0][0]:.4f})")