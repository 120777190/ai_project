# src/core/agent/state.py
# ====== 状态定义 ======

from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    question: str
    documents: List[Dict[str, str]]
    first_answer: str
    final_answer: str
    extra_prompt: str
    supervision_result: Dict[str, Any]
    debug_info: Dict[str, Any]