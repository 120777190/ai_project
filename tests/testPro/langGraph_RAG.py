import streamlit as st
import requests
import json
import os
import tempfile
from read_doc import read_file

#新增：导入配置模块
from config import Config

# ====== LangGraph 相关导入 ======
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any

# ====== 持久化配置 ======
DATA_DIR = os.getenv("DATA_DIR","data")
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
API_KEY = Config.API_KEY
URL = f"{Config.BASE_URL}/chat/completions"

# ====== 监督者Prompt ======
SUPERVISOR_PROMPT = """你是一个推理监督者。你的任务是分析思考者与用户之间的对话，判断思考者是否陷入了“纵向死胡同”或“交互无效循环”或“虚构推理产生幻觉结论”。

判断标准（满足任意一条即触发警报）：
1. 连续多次尝试同一方向的修复，且每次改动幅度小、方向单一
2. 反复评估同一选项的利弊，没有引入新的变量或替代方案
3. 同一主题下，多次输出的结构和表达高度相似，核心逻辑未变
4. 在多步骤推理中，反复推导同一卡点，没有尝试跳过或换方向
5. 用户发送的内容中包含重复的信息（如反复提问相同问题、反复强调同一个现象）
6. 用户表达了对当前方向的否定态度（如“还是不对”“不是这个问题”“方向错了”等）
7. 思考者输出的任何结论，如果是基于惯性、直觉或常见假设得出的，必须要求其返回文档原文或数据来源作为事实依据进行可靠性确认。若结论无法追溯到具体来源，视为不可靠。
8. 如果思考者确实无法从上下文中找到直接事实依据，允许其基于理论进行推论，但必须：① 明确标注“此为推论，非事实”② 以提示方式告知用户“当前结论基于理论推导，请提供相关事实依据以佐证”③ 推论与已知事实矛盾时，必须优先说明矛盾点。

触发警报后的处理方式（按优先级排序）：
1. 横向思考（优先）：跳出当前局限，检索整个对话历史，找出所有被忽略的方向和线索，一一罗列
2. 纵向思考（次选）：沿着当前方向深入挖掘，追问“这个问题的根源是什么”，而非停留在表面
3. 外部信息检索（备选）：引导思考者向用户提出需要补充的信息，或通过联网搜索获取外部数据
4. 事实核查：如果怀疑思考者基于惯性得出结论，强制要求其提供文档原文或数据来源
5. 透明推理（新增）：如果确实无事实依据，允许推论，但必须明确告知用户这是推论，并请求提供佐证

输入：当前轮次的对话内容（用户输入 + 思考者输出），以及历史对话摘要（如有）。

输出格式（严格按以下JSON格式）：
{
  "triggered": true/false,
  "matched_rules": [],
  "reason": "简要说明触发原因",
  "intervention": {
    "direction": "lateral",  // 可选值: "lateral", "vertical", "external", "fact_check", "transparent_inference"
    "instruction": "具体的引导指令",
    "priority": 1
  }
}
"""

# ====== 监督者函数（保持不变） ======
def supervise(user_question, thinker_response):
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
        response = requests.post(URL, headers=headers, json=data, timeout=Config.SUPERVISOR_TIMEOUT)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        # ========== 关键修复开始 ==========
        # 1. 确保 parsed 是字典
        if not isinstance(parsed, dict):
            parsed = {}
        
        # 2. 确保 intervention 字段存在，且是一个字典
        if "intervention" not in parsed or parsed["intervention"] is None:
            parsed["intervention"] = {}  # 👈 强制补一个空字典

        # 3. 确保 triggered 字段存在（注意：不要用 `or False`，会丢失 true）
        if "triggered" not in parsed:
            parsed["triggered"] = False
        # ========== 关键修复结束 ==========

        return parsed

    except Exception as e:
        # 异常返回时，也保证结构完整
        return {
            "triggered": False,
            "error": str(e),
            "reason": "监督者调用失败",
            "intervention": {}  # 👈 这里也改成空字典，而不是包含 instruction 的复杂结构
        }

# ====== 思考者函数（纯函数，不操作 session_state） ======
def ask_ai_with_context(question, all_contents, extra_prompt=""):
    """基于多个文档内容回答问题，返回答案字符串"""
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
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户问题：{question}\n回答："}
        ],
        "stream": False
    }
    try:
        response = requests.post(URL, headers=headers, json=data, timeout=Config.API_TIMEOUT)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"请求出错：{e}"

# ============================================================
# 新增：LangGraph 定义
# ============================================================

# 1. 定义状态
class AgentState(TypedDict):
    question: str
    documents: List[Dict[str, str]]
    first_answer: str          # 第一次思考的答案
    final_answer: str          # 最终答案（可能被干预修正）
    extra_prompt: str          # 监督者给的额外引导
    supervision_result: Dict[str, Any]  # 监督者的完整输出
    debug_info: Dict[str, Any] # 用于调试面板

# 2. 节点：思考者（第一次思考）
def reasoning_node(state: AgentState):
    question = state["question"]
    docs = state["documents"]
    answer = ask_ai_with_context(question, docs)
    # 只存 first_answer，final_answer 暂不设置
    return {"first_answer": answer, "final_answer": answer}

# 3. 节点：监督者（判断是否需要干预）
def supervisor_node(state: AgentState):
    question = state["question"]
    first_ans = state.get("first_answer", "")
    if not first_ans:
        # 极端情况，直接返回不触发
        return {"supervision_result": {"triggered": False}}
    result = supervise(question, first_ans)
    return {"supervision_result": result}

# 4. 节点：干预执行者（根据监督指令再次思考）
def intervene_node(state: AgentState):
    instruction = state["supervision_result"].get("intervention", {}).get("instruction", "")
    question = state["question"]
    docs = state["documents"]
    # 带着 extra_prompt 重新调用思考者
    second_answer = ask_ai_with_context(question, docs, extra_prompt=f"\n\n【监督者建议】{instruction}")
    return {"final_answer": second_answer}

# 5. 路由函数：根据监督结果决定下一步
def route_after_supervision(state: AgentState) -> str:
    result = state.get("supervision_result", {})
    if result.get("triggered", False):
        return "intervene"
    else:
        return "end"

# 6. 编译 LangGraph 图
workflow = StateGraph(AgentState)
workflow.add_node("reasoning", reasoning_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("intervene", intervene_node)

workflow.set_entry_point("reasoning")
workflow.add_edge("reasoning", "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_after_supervision,
    {
        "intervene": "intervene",
        "end": END
    }
)
workflow.add_edge("intervene", END)

#优化：把此处的硬加载模式改为懒加载，避免在调用模块或测试时反复加载影响开销
#agent_app = workflow.compile()

# ============================================================
# 懒加载：获取编译好的 LangGraph 应用
# ============================================================

def get_agent_app():
    """
    懒加载方式获取编译好的 LangGraph 应用。
    第一次调用时编译，后续调用直接返回缓存的实例。
    """
    # 检查函数属性 _app 是否存在，如果不存在则编译
    if not hasattr(get_agent_app, "_app"):
        # 构建工作流图
        workflow = StateGraph(AgentState)
        workflow.add_node("reasoning", reasoning_node)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("intervene", intervene_node)

        workflow.set_entry_point("reasoning")
        workflow.add_edge("reasoning", "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            route_after_supervision,
            {
                "intervene": "intervene",
                "end": END
            }
        )
        workflow.add_edge("intervene", END)

        # 编译并缓存到函数属性中
        get_agent_app._app = workflow.compile()
    
    # 返回缓存的实例
    return get_agent_app._app

# ============================================================
# 新的 think_with_supervision 函数（使用 LangGraph）
# ============================================================
def think_with_supervision(question, all_contents):
    """
    使用 LangGraph 图执行带监督的思考流程
    返回最终答案，并更新 session_state 中的历史与调试信息
    """
    # 初始化状态
    initial_state = {
        "question": question,
        "documents": all_contents,
        "first_answer": "",
        "final_answer": "",
        "extra_prompt": "",
        "supervision_result": {},
        "debug_info": {}
    }

    # 运行图
    agent_app = get_agent_app()
    final_state = agent_app.invoke(initial_state)
    
    # ====== 调试打印：检查 final_state 的类型和内容 ======
    print("=" * 50)
    print("🔍 final_state 类型:", type(final_state))
    print("🔍 final_state 是否为 None:", final_state is None)
    if final_state is not None:
        print("🔍 final_state 的 keys:", final_state.keys() if isinstance(final_state, dict) else "不是字典")
        print("🔍 supervision_result 的值:", final_state.get("supervision_result", "【key不存在】"))
    print("=" * 50)
    
    # 提取结果
    first_answer = final_state.get("first_answer", "")
    final_answer = final_state.get("final_answer", "")
    supervision_result = final_state.get("supervision_result", {}) or {}

    # 构建调试日志（与原格式保持一致）
    debug_log = { 
        "round": 1,
        "user_question": question,
        "thinker_first_response": first_answer,
        "supervisor_input": f"用户问题：{question}\n思考者回答：{first_answer}",
        "supervisor_output": supervision_result,
        "intervention_triggered": supervision_result.get("triggered", False),
        "intervention_instruction": supervision_result.get("intervention", {}).get("instruction", ""),
        "thinker_second_response": final_answer if supervision_result.get("triggered") else "",
        "final_answer": final_answer
    }
    st.session_state.supervision_debug = debug_log

    # 更新监督者日志（简洁版，用于界面显示）
    if supervision_result.get("triggered", False):
        st.session_state.supervision_log = {
            "triggered": True,
            "reason": supervision_result.get("reason", ""),
            "direction": supervision_result.get("intervention", {}).get("direction", ""),
            "instruction": supervision_result.get("intervention", {}).get("instruction", "")
        }
    else:
        st.session_state.supervision_log = {
            "triggered": False,
            "reason": "未触发警报"
        }

    # 追加对话历史（只追加一次，使用 final_answer）
    if "history" not in st.session_state:
        st.session_state.history = []
    history_entry = {
        "question": question,
        "answer": final_answer,
        "supervised": supervision_result.get("triggered", False)
    }
    if supervision_result.get("triggered"):
        history_entry["intervention"] = supervision_result.get("intervention", {}).get("instruction", "")
    st.session_state.history.append(history_entry)
    save_history(st.session_state.history)

    return final_answer

# ============================================================
# 以下为 Streamlit 界面（完全保持不变）
# ============================================================

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

# 文件上传
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

# 文档列表
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

# 问答区域
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

# 监督者调试面板
st.divider()
with st.expander("🔍 监督者调试面板（展开查看完整运行轨迹）"):
    if st.session_state.supervision_debug:
        st.json(st.session_state.supervision_debug)
    else:
        st.caption("暂无监督者日志，请先进行一次问答")

# 监督者干预记录
if st.session_state.supervision_log.get("triggered", False):
    log = st.session_state.supervision_log
    st.info(f"⚡ 监督者触发干预\n\n**原因：** {log.get('reason', '')}\n\n**指令：** {log.get('instruction', '')}")

# 对话历史
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