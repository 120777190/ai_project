# src/services/chat_service.py
# ====== 问答服务 ======

from src.core.agent.graph import get_agent_app

class ChatService:
    """问答服务"""
    
    def __init__(self):
        self.agent_app = get_agent_app()
    
    def ask(self, question: str) -> dict:
        """执行问答：参数全部走配置，调用方无需关心检索细节"""
        initial_state = {
            "question": question,
            "documents": [],
            "first_answer": "",
            "final_answer": "",
            "extra_prompt": "",
            "supervision_result": {},
            "debug_info": {}
        }
        
        final_state = self.agent_app.invoke(initial_state)
        supervision_result = final_state.get("supervision_result", {}) or {}
        
        return {
            "question": question,
            "answer": final_state.get("final_answer", ""),
            "supervised": supervision_result.get("triggered", False),
            "supervision_reason": supervision_result.get("reason", ""),
            "intervention_instruction": supervision_result.get("intervention", {}).get("instruction", "")
        }