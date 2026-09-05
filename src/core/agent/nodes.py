# src/core/agent/nodes.py
# ====== 节点函数 ======

from src.core.llm.thinker import ask_ai_with_context
from src.core.llm.supervisor import supervise
from src.core.agent.state import AgentState


def reasoning_node(state: AgentState):
    """思考者节点"""
    question = state["question"]
    docs = state["documents"]
    answer = ask_ai_with_context(question, docs)
    return {"first_answer": answer, "final_answer": answer}


def supervisor_node(state: AgentState):
    """监督者节点"""
    question = state["question"]
    first_ans = state.get("first_answer", "")
    if not first_ans:
        return {"supervision_result": {"triggered": False}}
    result = supervise(question, first_ans)
    return {"supervision_result": result}


def intervene_node(state: AgentState):
    """干预执行节点"""
    supervision_result = state.get("supervision_result") or {}
    instruction = supervision_result.get("intervention", {}).get("instruction", "")
    question = state["question"]
    docs = state["documents"]
    second_answer = ask_ai_with_context(question, docs, extra_prompt=f"\n\n【监督者建议】{instruction}")
    return {"final_answer": second_answer}