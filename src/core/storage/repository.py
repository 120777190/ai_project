# src/core/storage/repository.py
# ====== 持久化操作 ======

import json
import os
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("Repository")

DATA_DIR = settings.DATA_DIR
DOCS_FILE = os.path.join(DATA_DIR, "documents.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
VECTORS_FILE = os.path.join(DATA_DIR, "vectors.json")

if not os.path.exists(DATA_DIR):
    logger.debug(f"创建数据目录: {DATA_DIR}")
    os.makedirs(DATA_DIR)


def load_documents():
    if os.path.exists(DOCS_FILE):
        try:
            with open(DOCS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"📂 成功加载 {len(data)} 个文档")
                return data
        except Exception as e:
            logger.error(f"❌ 读取文档失败: {str(e)}")
            return []
    return []


def save_documents(docs):
    try:
        with open(DOCS_FILE, 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        logger.debug(f"💾 成功保存 {len(docs)} 个文档")
    except Exception as e:
        logger.error(f"❌ 保存文档失败: {str(e)}")


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"📂 成功加载 {len(data)} 条历史记录")
                return data
        except Exception as e:
            logger.error(f"❌ 读取历史失败: {str(e)}")
            return []
    return []


def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.debug(f"💾 成功保存 {len(history)} 条历史记录")
    except Exception as e:
        logger.error(f"❌ 保存历史失败: {str(e)}")


def load_vectors():
    if not os.path.exists(VECTORS_FILE):
        logger.warning(f"⚠️ 向量文件不存在: {VECTORS_FILE}")
        return []
    try:
        with open(VECTORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"📂 成功加载向量文件，共 {len(data)} 条记录")
            return data
    except Exception as e:
        logger.error(f"❌ 读取向量文件失败: {str(e)}")
        return []


def save_vectors(vectors):
    try:
        with open(VECTORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(vectors, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 向量数据已持久化到 {VECTORS_FILE}，共 {len(vectors)} 条")
    except Exception as e:
        logger.error(f"❌ 保存向量文件失败: {str(e)}")