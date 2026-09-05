# src/core/storage/repository.py
# ====== 持久化操作 ======

import json
import os
from src.config.settings import settings

DATA_DIR = settings.DATA_DIR
DOCS_FILE = os.path.join(DATA_DIR, "documents.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def load_documents():
    if os.path.exists(DOCS_FILE):
        try:
            with open(DOCS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_documents(docs):
    with open(DOCS_FILE, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)