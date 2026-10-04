# src/presentation/streamlit_app.py
# ====== Streamlit 界面 ======

import streamlit as st
import os
import tempfile

from src.services.chat_service import ChatService
import src.core.storage.repository as repository
from src.utils.document_parser import parse_document
from src.core.llm.embedder import get_embedding
from src.rag.text_splitter import chunk_text
from src.utils.logger import get_logger # 👈 新增日志导入

logger = get_logger("StreamlitUI") # 👈 初始化日志

def render_ui():
    """渲染整个 UI 界面"""
    
    logger.info("====== 开始渲染 UI 界面 ======") # 👈 日志
    
    chat_service = ChatService()
    
    st.title("📚 知识库问答助手")
    st.markdown("上传一个或多个文档，然后提问")
    
    # ====== 初始化 session_state ======
    if "documents" not in st.session_state:
        st.session_state.documents = repository.load_documents()
    if "history" not in st.session_state:
        st.session_state.history = repository.load_history()
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    # 👇 加回监督者相关的 session_state
    if "supervision_log" not in st.session_state:
        st.session_state.supervision_log = {}
    if "supervision_debug" not in st.session_state:
        st.session_state.supervision_debug = {}
    
    # ====== 文件上传 ======
    uploaded_files = st.file_uploader(
        "上传文档（支持 .txt / .pdf / .docx）",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_files:
        logger.info(f"检测到上传文件，共 {len(uploaded_files)} 个，开始处理...") # 👈 日志
        new_count = 0
        #准备一个列表，存切分好的内容（带溯源信息）
        new_chunks_with_source = []
        for file in uploaded_files:
            if any(doc["name"] == file.name for doc in st.session_state.documents):
                logger.info(f"文件 {file.name} 已存在，跳过") # 👈 日志
                continue
            
            with st.spinner(f"正在解析：{file.name}"):
                content = parse_document(file.getvalue(), filename=file.name)
            
            if "出错" not in content and "不支持" not in content:
                st.session_state.documents.append({
                    "name": file.name,
                    "content": content
                })
                repository.save_documents(st.session_state.documents)
                chunks = chunk_text(content)
                for chunk in chunks:
                    new_chunks_with_source.append({
                        "source": file.name,
                        "text": chunk
                    })
                new_count += 1
                logger.info(f"文件 {file.name} 解析并切分成功，产生 {len(chunks)} 个文本块") # 👈 日志
            else:
                logger.warning(f"文件 {file.name} 解析失败或格式不支持") # 👈 日志

        #提取切分好的文本
        if new_chunks_with_source: # 👈 新增判空保护，防止无新文档时API报错
            chunk_texts = [item["text"] for item in new_chunks_with_source]
            logger.info(f"准备对 {len(chunk_texts)} 个文本块进行向量化") # 👈 日志
            
            #发给大模型并接收返回的向量数组
            embeddings = get_embedding(chunk_texts)
            
            if embeddings is None: # 👈 新增API失败保护
                logger.error("❌ 向量化失败，get_embedding 返回 None！请检查 Embedding API 配置")
                st.error("❌ 致命错误：向量化 API 调用失败，请检查终端日志！")
                st.stop()

            #数据重组
            final_data = []
            for i, item in enumerate(new_chunks_with_source):
                final_data.append({
                    "source":item["source"],
                    "text":item["text"],
                    "embedding":embeddings[i] #向量 、文本、溯源对应
                })
            #持久化
            repository.save_vectors(final_data)
            logger.info(f"✅ 向量化并持久化成功，共保存 {len(final_data)} 条向量数据") # 👈 日志
        
        if new_count > 0:
            st.success(f"✅ 成功加载 {new_count} 个文档，当前共 {len(st.session_state.documents)} 个文档,共切割{len(new_chunks_with_source)}块")
    
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
                repository.save_documents(st.session_state.documents)
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
            repository.save_documents(st.session_state.documents)
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
            logger.info(f"====== 用户发起提问: {question} ======") # 👈 日志
            with st.spinner("AI 正在综合所有文档思考..."):
                # 👇 核心修改：只传 question，后端自动检索
                logger.info("开始调用 ChatService (LangGraph 图执行)") # 👈 日志
                result = chat_service.ask(question)
                logger.info("ChatService 图执行完毕，收到最终结果") # 👈 日志
                
                # 👇 更新监督者日志（从 result 中提取）
                st.session_state.supervision_log = {
                    "triggered": result.get("supervised", False),
                    "reason": result.get("supervision_reason", ""),
                    "instruction": result.get("intervention_instruction", "")
                }
                
                # 👇 构建调试日志
                st.session_state.supervision_debug = {
                    "user_question": question,
                    "final_answer": result["answer"],
                    "intervention_triggered": result.get("supervised", False),
                    "intervention_instruction": result.get("intervention_instruction", ""),
                    "supervisor_output": {
                        "triggered": result.get("supervised", False),
                        "reason": result.get("supervision_reason", "")
                    }
                }
                
                # 记录历史
                history_entry = {
                    "question": result["question"],
                    "answer": result["answer"],
                    "supervised": result.get("supervised", False)
                }
                if result.get("intervention_instruction"):
                    history_entry["intervention"] = result["intervention_instruction"]
                st.session_state.history.append(history_entry)
                repository.save_history(st.session_state.history)
            
            st.write("🤖 回答：")
            st.write(result["answer"])
    
    if not send_clicked and question:
        st.caption("💡 输入问题后，点击「发送」按钮提问")
    
    # ====== 👇 监督者调试面板（加回来） ======
    st.divider()
    with st.expander("🔍 监督者调试面板（展开查看完整运行轨迹）"):
        if st.session_state.supervision_debug:
            st.json(st.session_state.supervision_debug)
        else:
            st.caption("暂无监督者日志，请先进行一次问答")
    
    # ====== 👇 监督者干预记录（加回来） ======
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
            repository.save_history(st.session_state.history)
            st.rerun()