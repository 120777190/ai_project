import streamlit as st
import requests
import json
import os
import tempfile
from src.utils.read_doc import read_file

# ====== 配置 ======
API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"
URL = "https://api.deepseek.com/v1/chat/completions"

# ====== 持久化配置 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
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

# ====== 问答函数 ======
def ask_ai_with_context(question, all_contents):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    combined = ""
    for doc in all_contents:
        combined += f"\n\n【文档：{doc['name']}】\n{doc['content']}"
    
    system_prompt = f"""请基于以下多个文档的内容回答用户的问题。

注意事项：
1. 如果多个文档中有相关信息，可以综合引用。
2. 如果文档中的信息与用户问题在时间、人物、事件主体上存在不一致，请先指出这种不一致。
3. 如果所有文档中都没有相关信息，请说"文档中没有提到这个问题"。
4. 不要编造信息。

=== 所有文档内容 ===
{combined}
=== 文档内容结束 ===
"""
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": system_prompt + f"\n\n用户问题：{question}\n回答："}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=60)
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        
        st.session_state.history.append({
            "question": question,
            "answer": answer
        })
        save_history(st.session_state.history)  # 持久化历史
        
        return answer
    except Exception as e:
        return f"请求出错：{e}"

# ====== 界面 ======
st.set_page_config(page_title="RAG 知识库问答", page_icon="📚")
st.title("📚 知识库问答助手")
st.markdown("上传一个或多个文档，然后提问")

# 从文件加载数据
if "documents" not in st.session_state:
    st.session_state.documents = load_documents()
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ====== 文件上传 ======
uploaded_files = st.file_uploader(
    "上传文档（支持 .txt / .pdf / .docx）", 
    type=["txt", "pdf", "docx"],
    accept_multiple_files=True,
    key=f"file_uploader_{st.session_state.uploader_key}"
)

if uploaded_files:
    new_count = 0
    for file in uploaded_files:
        if any(doc["name"] == file.name for doc in st.session_state.documents):
            continue
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        
        with st.spinner(f"正在解析：{file.name}"):
            content = read_file(tmp_path)
        
        os.unlink(tmp_path)
        
        if "出错" not in content and "不支持" not in content:
            st.session_state.documents.append({
                "name": file.name,
                "content": content
            })
            save_documents(st.session_state.documents)  # 持久化文档
            new_count += 1
    
    if new_count > 0:
        st.success(f"✅ 成功加载 {new_count} 个文档，当前共 {len(st.session_state.documents)} 个文档")

# ====== 文档列表 ======
if st.session_state.documents:
    st.divider()
    st.subheader(f"📄 已加载文档（{len(st.session_state.documents)} 个）")
    
    for i, doc in enumerate(st.session_state.documents):
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.text(f"{i+1}. {doc['name']}（{len(doc['content'])} 个字符）")
        
        if col2.button("📖 预览", key=f"preview_btn_{i}"):
            st.session_state[f"preview_state_{i}"] = not st.session_state.get(f"preview_state_{i}", False)
            st.rerun()
        
        if col3.button("🗑️ 删除", key=f"del_btn_{i}"):
            st.session_state.documents.pop(i)
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith(f"preview_state_{i}") or k.startswith(f"content_area_{i}")]
            for k in keys_to_remove:
                del st.session_state[k]
            save_documents(st.session_state.documents)  # 持久化文档
            st.session_state.uploader_key += 1
            st.rerun()
        
        if st.session_state.get(f"preview_state_{i}", False):
            with st.expander(f"📄 {doc['name']} 内容预览", expanded=True):
                st.text_area(
                    label="文档内容",
                    value=doc['content'],
                    height=200,
                    disabled=True,
                    key=f"content_area_{i}"
                )
    
    if st.button("🗑️ 清空所有文档", key="clear_all"):
        st.session_state.documents = []
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("preview_state_") or k.startswith("content_area_")]
        for k in keys_to_remove:
            del st.session_state[k]
        save_documents(st.session_state.documents)  # 持久化文档
        st.session_state.uploader_key += 1
        st.rerun()

# ====== 问答区域 ======
st.divider()
question = st.text_input("💬 输入你的问题：", placeholder="例如：这些文档主要讲了什么？")
send_clicked = st.button("📤 发送", key="send_btn", type="primary")

if send_clicked and question:
    if not st.session_state.documents:
        st.warning("请先上传文档")
    else:
        with st.spinner("AI 正在综合所有文档思考..."):
            answer = ask_ai_with_context(question, st.session_state.documents)
        st.write("🤖 回答：")
        st.write(answer)

if not send_clicked and question:
    st.caption("💡 输入问题后，点击「发送」按钮提问")

# ====== 对话历史 ======
if st.session_state.history:
    st.divider()
    st.subheader("📜 对话历史")
    for i, entry in enumerate(st.session_state.history):
        st.markdown(f"**Q{i+1}:** {entry['question']}")
        st.markdown(f"**A{i+1}:** {entry['answer']}")
        st.markdown("---")
    
    if st.button("🗑️ 清空历史", key="clear_history"):
        st.session_state.history = []
        save_history(st.session_state.history)  # 持久化历史