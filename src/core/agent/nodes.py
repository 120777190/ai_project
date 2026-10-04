# src/core/agent/nodes.py
# ====== 节点函数 ======

from src.config.settings import settings
from src.core.llm.thinker import ask_ai_with_context
from src.core.llm.supervisor import supervise
from src.core.llm.embedder import get_embedding
from src.core.agent.state import AgentState
from src.rag.retriever import search_vectors
from src.utils.logger import get_logger

logger = get_logger("AgentNode")


def retrieve_node(state: AgentState):
    """动态检索节点：从配置读取参数，内部完成检索"""
    logger.info("--- 进入 [retrieve_node] ---")
    question = state["question"]

    # 从配置读取参数
    top_k = settings.RAG_TOP_K
    threshold = settings.RAG_SCORE_THRESHOLD

    # 问题向量化
    query_emb_list = get_embedding([question])
    if not query_emb_list:
        logger.error("❌ 问题向量化失败，无法检索")
        return {"documents": []}
    
    query_emb = query_emb_list[0]
    logger.info(f"问题向量化成功，维度: {len(query_emb)}，开始检索...")

    # 调用独立检索模块（已完成排序、过滤、截断）
    results = search_vectors(
        query_embedding=query_emb,
        top_k=top_k,
        score_threshold=threshold
    )

    # 转换为 thinker.py 期望的格式
    docs = [{"name": r["source"], "content": r["text"]} for r in results]
    logger.info(f"检索节点执行完毕，准备向下游传递 {len(docs)} 个文档块")
    return {"documents": docs}


def reasoning_node(state: AgentState):
    """思考者节点"""
    logger.info("--- 进入 [reasoning_node] (思考者) ---")
    question = state["question"]
    docs = state["documents"]
    logger.debug(f"思考者收到 {len(docs)} 个文档块")
    
    answer = ask_ai_with_context(question, docs)
    
    logger.info("思考者回答生成完毕")
    return {"first_answer": answer, "final_answer": answer}


def supervisor_node(state: AgentState):
    """监督者节点"""
    logger.info("--- 进入 [supervisor_node] (监督者) ---")
    question = state["question"]
    first_ans = state.get("first_answer", "")
    if not first_ans:
        logger.warning("没有首次回答，监督者跳过")
        return {"supervision_result": {"triggered": False}}
    
    result = supervise(question, first_ans)
    logger.info(f"监督者判断完毕，触发干预: {result.get('triggered', False)}")
    return {"supervision_result": result}


def intervene_node(state: AgentState):
    """干预执行节点"""
    logger.info("--- 进入 [intervene_node] (干预执行) ---")
    supervision_result = state.get("supervision_result") or {}
    instruction = supervision_result.get("intervention", {}).get("instruction", "")
    question = state["question"]
    docs = state["documents"]
    
    logger.info(f"接收监督建议: {instruction[:50]}...") # 打印前50字
    second_answer = ask_ai_with_context(question, docs, extra_prompt=f"\n\n【监督者建议】{instruction}")
    
    logger.info("干预回答生成完毕")
    return {"final_answer": second_answer}