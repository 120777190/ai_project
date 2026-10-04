# src/config/settings.py
# ====== 配置加载 ======

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    """应用配置"""
    
    # API 配置
    API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    #配置向量模型（智谱 API 信息）
    EMBEADDER_API_KEY = os.getenv("EMBEADDER_API_KEY", "")
    EMBEADDER_URL = os.getenv("EMBEADDER_URL", "https://open.bigmodel.cn/api/paas/v4/embeddings")
    
    # 模型配置
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-chat")
    EMBEADDER_DEFAULT_MODE = os.getenv("EMBEADDER_DEFAULT_MODE", "embedding-3")
    
    # 超时配置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    SUPERVISOR_TIMEOUT = int(os.getenv("SUPERVISOR_TIMEOUT", "30"))

    #切割配置
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    OVERLAP = int(os.getenv("OVERLAP", "50"))

    # ====== RAG 检索参数 ======
    RAG_FETCH_K = int(os.getenv("RAG_FETCH_K", "20"))               # 初步广撒网的条数（如果后续用 FAISS 或 Chroma 会用到，JSON方案暂时不用）
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))                 # 最终发给大模型的上限数量
    RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))      # 相似度阈值，低于此值的被丢弃
    
    
    # 数据目录
    DATA_DIR = os.getenv("DATA_DIR", "data")
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        if not cls.API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置")


# 全局配置实例
settings = Settings()
