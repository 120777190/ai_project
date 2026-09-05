# app.py
# ====== 程序入口 ======

import sys
from pathlib import Path

# 添加 src 到 Python 路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st
from src.config.settings import settings
from src.presentation.streamlit_app import render_ui


def main():
    # 验证配置
    try:
        settings.validate()
    except ValueError as e:
        st.error(f"❌ 配置错误：{e}")
        st.stop()
    
    # 设置页面
    st.set_page_config(
        page_title="RAG 知识库问答",
        page_icon="📚",
        layout="wide"
    )
    
    # 渲染 UI
    render_ui()


if __name__ == "__main__":
    main()