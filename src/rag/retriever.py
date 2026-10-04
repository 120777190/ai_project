# src/rag/retriever.py
import math
import src.core.storage.repository as repository
from src.utils.logger import get_logger

logger = get_logger("Retriever")

def _cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot / (mag1 * mag2)

def search_vectors(query_embedding, top_k=5, score_threshold=0.75):
    logger.info(f"🔍 开始检索，阈值: {score_threshold}, 上限: {top_k}")
    vectors = repository.load_vectors()
    if not vectors:
        logger.warning("⚠️ 没有可检索的向量数据，直接返回空")
        return []

    scored = []
    for item in vectors:
        emb = item.get("embedding")
        if not emb: continue
        score = _cosine_similarity(query_embedding, emb)
        scored.append({"source": item.get("source", "未知"), "text": item.get("text", ""), "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    if scored:
        logger.info(f"📊 共计算 {len(scored)} 条相似度，最高得分: {scored[0]['score']:.4f}")

    results = []
    for item in scored:
        if item["score"] < score_threshold:
            logger.debug(f"🛑 遇到低于阈值({score_threshold})的项 ({item['score']:.4f})，提前终止")
            break
        if len(results) >= top_k:
            logger.debug(f"🛑 已达到上限 {top_k}，终止过滤")
            break
        results.append(item)
        
    logger.info(f"✅ 最终返回 {len(results)} 条检索结果")
    return results