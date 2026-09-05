import streamlit as st
import requests
import json
import os
import tempfile
from src.utils.read_doc import read_file

# ====== 持久化配置 ======
DATA_DIR = "data"
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

# ====== 配置 ======
API_KEY = "sk-1019c52f71664e7c9172f189192f7c7e"
URL = "https://api.deepseek.com/v1/chat/completions"

# ====== 监督者Prompt ======
SUPERVISOR_PROMPT = """你是一个推理监督者。你的任务是分析思考者与用户之间的对话，判断思考者是否陷入了“纵向死胡同”或“交互无效循环”。

判断标准（满足任意一条即触发警报）：
1. 连续多次尝试同一方向的修复，且每次改动幅度小、方向单一
2. 反复评估同一选项的利弊，没有引入新的变量或替代方案
3. 同一主题下，多次输出的结构和表达高度相似，核心逻辑未变
4. 在多步骤推理中，反复推导同一卡点，没有尝试跳过或换方向
5. 用户发送的内容中包含重复的信息（如反复提问相同问题、反复强调同一个现象）
6. 用户表达了对当前方向的否定态度（如“还是不对”“不是这个问题”“方向错了”等）

触发警报后的处理方式（按优先级排序）：
1. 横向思考（优先）：跳出当前局限，检索整个对话历史，找出所有被忽略的方向和线索，一一罗列
2. 纵向思考（次选）：沿着当前方向深入挖掘，追问“这个问题的根源是什么”，而非停留在表面
3. 外部信息检索（备选）：引导思考者向用户提出需要补充的信息，或通过联网搜索获取外部数据

输入：当前轮次的对话内容（用户输入 + 思考者输出），以及历史对话摘要（如有）。

输出格式（严格按以下JSON格式）：
{
  "triggered": true/false,
  "matched_rules": [],
  "reason": "简要说明触发原因",
  "intervention": {
    "direction": "lateral",
    "instruction": "具体的引导指令",
    "priority": 1
  }
}
"""

# ====== 监督者函数 ======
def supervise(user_question, thinker_response):
    """监督者：判断思考者是否陷入死胡同，并返回干预指令"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    input_text = f"用户问题：{user_question}\n思考者回答：{thinker_response}"
    
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": input_text}
    ]
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": False,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=30)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {
            "triggered": False,
            "error": str(e),
            "reason": "监督者调用失败",
            "intervention": {"direction": "", "instruction": "", "priority": 0}
        }

# ====== 思考者函数 ======
def ask_ai_with_context(question, all_contents, extra_prompt=""):
    """基于多个文档内容回答问题，可接受额外提示词"""
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
    
    if extra_prompt.strip():
        system_prompt += f"\n\n{extra_prompt}"
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户问题：{question}\n回答："}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=60)
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({
            "question": question,
            "answer": answer,
            "supervised": False
        })
        save_history(st.session_state.history)
        
        return answer
    except Exception as e:
        return f"请求出错：{e}"

# ====== 带监督的思考主流程 ======
def think_with_supervision(question, all_contents):
    """带监督的思考流程：思考 → 监督判断 → 如有必要，执行干预"""
    debug_log = {
        "round": 1,
        "user_question": question,
        "thinker_first_response": "",
        "supervisor_input": "",
        "supervisor_output": {},
        "intervention_triggered": False,
        "intervention_instruction": "",
        "thinker_second_response": "",
        "final_answer": ""
    }

    # 第一轮思考
    first_answer = ask_ai_with_context(question, all_contents)
    debug_log["thinker_first_response"] = first_answer

    # 监督者判断
    supervision_result = supervise(question, first_answer)
    debug_log["supervisor_input"] = f"用户问题：{question}\n思考者回答：{first_answer}"
    debug_log["supervisor_output"] = supervision_result

    if supervision_result.get("triggered", False):
        intervention = supervision_result.get("intervention", {})
        instruction = intervention.get("instruction", "")
        direction = intervention.get("direction", "lateral")

        debug_log["intervention_triggered"] = True
        debug_log["intervention_instruction"] = instruction

        st.session_state.supervision_log = {
            "triggered": True,
            "reason": supervision_result.get("reason", ""),
            "direction": direction,
            "instruction": instruction
        }

        # 第二次思考
        second_answer = ask_ai_with_context(
            question,
            all_contents,
            extra_prompt=f"\n\n【监督者建议】{instruction}"
        )
        debug_log["thinker_second_response"] = second_answer
        debug_log["final_answer"] = second_answer

        if st.session_state.history:
            st.session_state.history[-1]["supervised"] = True
            st.session_state.history[-1]["intervention"] = instruction
            save_history(st.session_state.history)

        st.session_state.supervision_debug = debug_log
        return second_answer
    else:
        debug_log["intervention_triggered"] = False
        debug_log["final_answer"] = first_answer

        st.session_state.supervision_log = {
            "triggered": False,
            "reason": "未触发警报"
        }

        st.session_state.supervision_debug = debug_log
        return first_answer

# ====== 界面 ======
st.set_page_config(page_title="RAG 知识库问答", page_icon="📚")
st.title("📚 知识库问答助手")
st.markdown("上传一个或多个文档，然后提问")

# 初始化
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
            answer = think_with_supervision(question, st.session_state.documents)
        st.write("🤖 回答：")
        st.write(answer)

if not send_clicked and question:
    st.caption("💡 输入问题后，点击「发送」按钮提问")

# ====== 监督者调试面板 ======
st.divider()
with st.expander("🔍 监督者调试面板（展开查看完整运行轨迹）"):
    if st.session_state.supervision_debug:
        st.json(st.session_state.supervision_debug)
    else:
        st.caption("暂无监督者日志，请先进行一次问答")

# ====== 监督者干预记录（简洁版） ======
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