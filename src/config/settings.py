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
    
    # 模型配置
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-chat")
    
    # 超时配置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    SUPERVISOR_TIMEOUT = int(os.getenv("SUPERVISOR_TIMEOUT", "30"))
    
    # 数据目录
    DATA_DIR = os.getenv("DATA_DIR", "data")
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        if not cls.API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置")


# 全局配置实例
settings = Settings()