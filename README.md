# 基于 LangGraph 的 RAG 智能问答系统

一个具备「思考者-监督者」双 Agent 协同机制的企业级 RAG 知识库问答系统。

## 📖 项目简介

本项目是一个基于 LangGraph 构建的 RAG（检索增强生成，Retrieval-Augmented Generation）智能问答系统。用户上传文档后，系统能基于文档内容回答问题，并内置一个「监督者」Agent 实时监控「思考者」的推理过程，当检测到推理陷入死胡同或缺乏事实依据时，自动触发 ReAct（推理+行动，Reasoning + Acting）反思机制进行纠错。

在 v1.1.0 版本中，系统引入了**动态检索节点**，实现了“广撒网召回 → 降序排序 → 阈值过滤 → Top-K 截断”的工业级检索逻辑，并全面接入了**全链路日志系统**，让每一步调试都有迹可循。

## ✨ 核心特性

- **双 Agent 协同机制**：思考者负责生成答案，监督者实时监控推理质量
- **ReAct 反思循环**：监督者触发干预时，系统自动带着纠正指令重新推理
- **8 条监督规则**：涵盖死循环检测、事实核查、透明推理等多种场景
- **动态 RAG 检索**：不设相似度下限，只设上限，确保优中选优，避免无关文档污染大模型上下文
- **企业级分层架构**：展示层、服务层、核心层、工具层职责清晰分离
- **全链路日志追踪**：涵盖文档上传、向量化、检索、生成的全流程 Debug 日志
- **多格式文档支持**：支持 .txt / .pdf / .docx 文档解析
- **数据持久化**：文档、历史记录、向量数据自动保存，重启不丢失
- **监督者调试面板**：可视化展示完整的监督运行轨迹

## 🏗 项目架构

```text
ai_project/
├── app.py                          # 程序入口
├── requirements.txt                # 依赖列表
├── .env                            # 环境变量（本地）
├── .env.example                    # 环境变量模板
│
├── src/                            # 源代码主目录
│   ├── config/                     # 配置层
│   │   └── settings.py             # 配置加载 (含 RAG 检索参数)
│   │
│   ├── core/                       # 核心业务逻辑
│   │   ├── agent/                  # Agent 相关
│   │   │   ├── state.py            # AgentState 状态定义
│   │   │   ├── nodes.py            # LangGraph 节点函数 (含 retrieve_node)
│   │   │   └── graph.py            # LangGraph 图定义（状态+节点+路由）
│   │   ├── llm/                    # LLM 调用
│   │   │   ├── thinker.py          # 思考者
│   │   │   ├── supervisor.py       # 监督者
│   │   │   └── embedder.py         # 向量化调用
│   │   └── storage/                # 存储层
│   │       └── repository.py       # 持久化操作 (JSON 读写)
│   │
│   ├── rag/                        # RAG 核心模块
│   │   ├── text_splitter.py        # 文本切分
│   │   └── retriever.py            # 动态检索器 (排序/过滤/截断)
│   │
│   ├── services/                   # 服务层
│   │   └── chat_service.py         # 问答服务编排
│   │
│   ├── presentation/               # 展示层
│   │   └── streamlit_app.py        # Streamlit 界面
│   │
│   └── utils/                      # 工具层
│       ├── document_parser.py      # 通用文档解析工具
│       └── logger.py               # 全局日志工具
│
└── data/                           # 数据存储目录
    ├── documents.json              # 原始文档
    ├── history.json                # 对话历史
    └── vectors.json                # 向量数据