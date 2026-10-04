# src/core/agent/graph.py
# ====== LangGraph 图定义模块 ======
# 职责：AgentState 定义、路由函数、图编译（懒加载）

from langgraph.graph import StateGraph, END

# 从同目录导入 thinker 和 supervisor
from src.core.agent.state import AgentState
from src.core.agent.nodes import (
    retrieve_node, reasoning_node, supervisor_node, intervene_node
)



# ======  路由函数：根据监督结果决定下一步 ======
def route_after_supervision(state: AgentState) -> str:
    result = state.get("supervision_result", {})
    if result.get("triggered", False):
        return "intervene"
    else:
        return "end"


# ======  懒加载：获取编译好的 LangGraph 应用 ======
def get_agent_app():
    """懒加载方式获取编译好的 LangGraph 应用"""
    if not hasattr(get_agent_app, "_app"):
        workflow = StateGraph(AgentState)

        #加入检索节点
        workflow.add_node("retrieve", retrieve_node)
        workflow.add_node("reasoning", reasoning_node)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("intervene", intervene_node)

        #图入口改为 retrieve
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "reasoning")
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

        get_agent_app._app = workflow.compile()
    return get_agent_app._app