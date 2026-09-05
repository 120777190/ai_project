# config.py
# ====== 配置加载模块 ======
# 作用：从 .env 文件中读取所有配置，并提供统一的配置对象供其他模块使用

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Config:
    """
    配置类，集中管理所有环境变量
    使用方式：Config.API_KEY
    """
    
    # ====== API 配置 ======
    API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    # ====== 模型配置 ======
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-chat")
    SUPERVISOR_MODEL = os.getenv("SUPERVISOR_MODEL", "deepseek-chat")
    THINKER_MODEL = os.getenv("THINKER_MODEL", "deepseek-chat")
    
    # ====== 数据路径 ======
    DATA_DIR = os.getenv("DATA_DIR", "data")
    
    # ====== 超时配置 ======
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
    SUPERVISOR_TIMEOUT = int(os.getenv("SUPERVISOR_TIMEOUT", "30"))
    
    # ====== 服务配置 ======
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    
    # ====== 验证配置是否完整 ======
    @classmethod
    def validate(cls):
        """检查必要配置是否存在，缺失时给出明确提示"""
        if not cls.API_KEY:
            raise ValueError(
                "❌ DEEPSEEK_API_KEY 未配置！\n"
                "请在项目根目录的 .env 文件中设置你的 API Key。"
            )
        return True

# 打印当前配置（不含敏感信息，仅用于调试）
if __name__ == "__main__":
    print("=" * 50)
    print("📋 当前配置（已脱敏）")
    print("=" * 50)
    print(f"API Key: {Config.API_KEY[:8]}...{Config.API_KEY[-4:] if len(Config.API_KEY) > 12 else '（已隐藏）'}")
    print(f"Base URL: {Config.BASE_URL}")
    print(f"默认模型: {Config.DEFAULT_MODEL}")
    print(f"数据目录: {Config.DATA_DIR}")
    print(f"API 超时: {Config.API_TIMEOUT}秒")
    print(f"监督者超时: {Config.SUPERVISOR_TIMEOUT}秒")
    print("=" * 50)