# ui.py
# ====== UI 模块 ======
# 职责：界面排布、组件布局、按钮事件、用户交互

import streamlit as st
import os
import tempfile

from src.utils.read_doc import read_file
from src.core.storage import load_documents, save_documents, load_history, save_history
from src.core.controller import think_with_supervision


def render_ui():
    """渲染整个 UI 界面"""
    
    # ====== 标题 ======
    st.title("📚 知识库问答助手")
    st.markdown("上传一个或多个文档，然后提问")
    
    # ====== 初始化 session_state ======
    if "documents" not in st.session_state:
        st.session_state.documents = load_documents()
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "supervision_log" not in st.session_state:
        st.session_state.supervision_log = {}
    if "supervision_debug" not in st.session_state:
        st.session_state.supervision_debug = {}
    
    # ====== 文件上传区域 ======
    uploaded_files = st.file_uploader(
        "上传文档（支持 .txt / .pdf / .docx）",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_files:
        new_count = 0
        for file in uploaded_files:
            # 检查是否已存在
            if any(doc["name"] == file.name for doc in st.session_state.documents):
                continue
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                tmp.write(file.getbuffer())
                tmp_path = tmp.name
            
            # 解析文档
            with st.spinner(f"正在解析：{file.name}"):
                content = read_file(tmp_path)
            
            os.unlink(tmp_path)
            
            if "出错" not in content and "不支持" not in content:
                st.session_state.documents.append({
                    "name": file.name,
                    "content": content
                })
                save_documents(st.session_state.documents)
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
                save_documents(st.session_state.documents)
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
            save_documents(st.session_state.documents)
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
                result = think_with_supervision(question, st.session_state.documents)
                
                # 更新对话历史到 session_state
                if "history" not in st.session_state:
                    st.session_state.history = []
                history_entry = {
                    "question": result["question"],
                    "answer": result["answer"],
                    "supervised": result["supervised"]
                }
                if result.get("intervention_instruction"):
                    history_entry["intervention"] = result["intervention_instruction"]
                st.session_state.history.append(history_entry)
                save_history(st.session_state.history)
                
                # 更新监督者日志
                st.session_state.supervision_log = {
                    "triggered": result["supervised"],
                    "reason": result.get("supervision_reason", ""),
                    "instruction": result.get("intervention_instruction", "")
                }
                
                # 构建调试日志
                st.session_state.supervision_debug = {
                    "user_question": result["question"],
                    "final_answer": result["answer"],
                    "intervention_triggered": result["supervised"],
                    "intervention_instruction": result.get("intervention_instruction", ""),
                    "supervisor_output": {
                        "triggered": result["supervised"],
                        "reason": result.get("supervision_reason", "")
                    }
                }
            
            st.write("🤖 回答：")
            st.write(result["answer"])
    
    if not send_clicked and question:
        st.caption("💡 输入问题后，点击「发送」按钮提问")
    
    # ====== 监督者调试面板 ======
    st.divider()
    with st.expander("🔍 监督者调试面板（展开查看完整运行轨迹）"):
        if st.session_state.supervision_debug:
            st.json(st.session_state.supervision_debug)
        else:
            st.caption("暂无监督者日志，请先进行一次问答")
    
    # ====== 监督者干预记录 ======
    if st.session_state.supervision_log.get("triggered", False):
        log = st.session_state.supervision_log
        st.info(f"⚡ 监督者触发干预\n\n**原因：** {log.get('reason', '')}\n\n**指令：** {log.get('instruction', '')}")
    
    # ====== 对话历史 ======
    if st.session_state.history:
        st.divider()
        st.subheader("📜 对话历史")
        for i, entry in enumerate(st.session_state.history):
            st.markdown(f"**Q{i+1}:** {entry['question']}")
            st.markdown(f"**A{i+1}:** {entry['answer']}")
            if entry.get("supervised", False):
                st.caption(f"⚡ 已由监督者干预")
            st.markdown("---")
        
        if st.button("🗑️ 清空历史", key="clear_history"):
            st.session_state.history = []
            save_history(st.session_state.history)
            st.rerun()