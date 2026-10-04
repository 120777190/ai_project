# src/core/llm/embedder.py
import requests
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("Embedder")

def get_embedding(texts):
    logger.info(f"开始调用 Embedding API，共 {len(texts)} 条文本")
    headers = {
        "Authorization": f"Bearer {settings.EMBEADDER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": settings.EMBEADDER_DEFAULT_MODE,
        "input": texts
    }
    
    try:
        response = requests.post(settings.EMBEADDER_URL, headers=headers, json=data)
        logger.debug(f"API 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            datas = response.json()["data"]
            embeddings = [i["embedding"] for i in datas]
            if embeddings and len(embeddings) > 0:
                logger.info(f"✅ 向量化成功，返回 {len(embeddings)} 个向量，维度: {len(embeddings[0])}")
            return embeddings
        else:
            logger.error(f"❌ API 请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ API 请求发生异常: {str(e)}")
        return None