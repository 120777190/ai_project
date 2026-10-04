# 更新日志

本项目所有重要变更都会记录在此文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased] - 未发布

### 计划新增
- 基于大模型的多维度评估者模块（相关性、完整性、幻觉检测、满意度）
- 可插拔的检索策略（多种分块方案、向量模型、检索方式对比）
- FastAPI 接口，支持外部系统调用
- Docker 容器化部署
- 替换底层向量存储为 FAISS / Chroma 等专业向量数据库
- 引入 Rerank 重排序模型，提升检索精准度
- 增加多轮对话记忆（Memory）与查询重写（Query Rewrite）
- 流式输出（Streaming）与引用溯源展示

## [1.1.0] - 2026-10-04

### Added（新增）
- 全局日志模块 `src/utils/logger.py`，实现 VS Code 终端全链路 Debug 轨迹追踪
- 独立 RAG 检索模块 `src/rag/retriever.py`，实现 `search_vectors` 核心算法：
  - 支持余弦相似度计算。
  - 实现“降序排序 -> 阈值过滤（不设下限） -> Top-K 截断”的高质量检索逻辑。
- `AgentState` 新增 `retrieve_node` 节点，将动态检索纳入 LangGraph 工作流。
- `settings.py` 新增 RAG 检索配置项：`RAG_FETCH_K`、`RAG_TOP_K`、`RAG_SCORE_THRESHOLD`。

### Changed（变更）
- 重构 RAG 检索流程：`LangGraph` 图的入口由 `reasoning` 改为 `retrieve`，实现检索与生成的解耦。
- 优化配置管理：将 `top_k` 和 `score_threshold` 等调优参数从 UI 层收拢至 `settings.py`，避免用户误操作。
- 精简前端调用：`Streamlit` 不再向后端传递全量 `documents`，只传 `question`，由后端按需检索。
- 重构持久化模块 `repository.py`：仅保留纯粹的 JSON 存取职责，并增加完整的操作日志。

### Fixed（修复）
- 修复 `state.py` 中 `top_k` 和 `score_threshold` 语法定义错误（缺少冒号）。
- 修复 `nodes.py` 中 `retrieve_node` 调用 `repository.search_vectors` 的 `AttributeError`（迁移至 `retriever.py`）。
- 修复 `repository.py` 缺少 `load_documents` 和 `load_history` 等基础方法的 `AttributeError`。
- 修复 `nodes.py` 中缺少 `supervisor_node` 引发的 `ImportError`。
- 修复文档上传时，Embedding API 失败导致 Streamlit 页面崩溃的问题（增加空值拦截与明确报错）。
- 修复检索节点因相似度阈值（0.75）设置过高，导致匹配结果全被过滤、大模型无资料可用的空上下文问题。

## [1.0.0] - 2026-09-10

### Added（新增）
- 「思考者-监督者」双 Agent 协同机制
- 基于 LangGraph 的 ReAct 反思循环
- 监督者 8 条判断规则（死循环检测、事实核查、透明推理等）
- 多格式文档解析支持（.txt / .pdf / .docx）
- 文档和对话历史的 JSON 持久化
- 监督者调试面板，可视化运行轨迹
- 企业级分层架构（config / core / services / presentation / utils）
- 通用文档解析工具 `document_parser.py`
- 配置外移（.env + settings.py）
- LangGraph 懒加载优化
- Git 版本控制初始化
- README 项目说明文档

### Changed（变更）
- 将原单文件项目重构为企业级分层架构
- 监督者数据清洗逻辑，确保字段结构完整
- 导入路径统一为 `src.xxx` 格式

### Fixed（修复）
- 修复 `supervision_result` 为 `None` 导致的 `AttributeError`
- 修复 LangGraph 节点数据传递的结构完整性问题
- 修复监督者界面功能缺失问题（调试面板 + 干预记录）

### Security（安全）
- 将 API Key 从代码中移至 `.env` 文件
- 添加 `.gitignore` 防止敏感信息泄露

### Removed（移除）
- 移除旧版单文件 `langGraph_RAG.py`，功能已迁移至 `src/` 分层架构

## [0.2.0] - 2026-08-25

### Added
- LangGraph 框架集成
- 懒加载编译机制（`get_agent_app()`）
- 状态管理（`AgentState`）
- 条件路由（`route_after_supervision`）

### Changed
- 将双模型协作逻辑从普通函数调用重构为 LangGraph 图结构
- 监督者从「单一判断」升级为「条件边 + 干预节点」

### Fixed
- 修复监督者返回 `None` 时的程序崩溃问题

## [0.1.0] - 2026-08-20

### Added
- 项目初始原型
- 基础 RAG 问答功能
- 双模型协作的初步实现（思考者 + 监督者）
- Streamlit 基础界面
- 多格式文档解析
- JSON 持久化存储