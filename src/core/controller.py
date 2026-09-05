# core/controller.py
# ====== 控制器模块 ======
# 职责：统一的后端调度接口，同时为 UI 和 API 提供服务

from src.core.agent.graph import get_agent_app


def think_with_supervision(question, all_contents):
    """
    核心调度函数：执行完整的监督推理流程
    
    参数：
        question: str - 用户问题
        all_contents: List[Dict] - 文档列表
    
    返回：
        dict: {
            "question": str,
            "answer": str,
            "supervised": bool,
            "supervision_reason": str,
            "intervention_instruction": str
        }
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

    # 获取并执行 LangGraph 应用
    agent_app = get_agent_app()
    final_state = agent_app.invoke(initial_state)

    # 提取结果（带安全兜底）
    first_answer = final_state.get("first_answer", "")
    final_answer = final_state.get("final_answer", "")
    supervision_result = final_state.get("supervision_result", {}) or {}

    # 构建统一返回结果（不包含 session_state，便于 API 复用）
    result = {
        "question": question,
        "answer": final_answer,
        "supervised": supervision_result.get("triggered", False),
        "supervision_reason": supervision_result.get("reason", ""),
        "intervention_instruction": supervision_result.get("intervention", {}).get("instruction", "")
    }

    return result