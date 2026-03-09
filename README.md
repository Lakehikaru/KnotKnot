# Agentic RAG Document Generator v2.1

基于 Agentic RAG 的多智能体文档生成系统 - 最小可扩展实现

## ✨ 特性

- ✅ **Agentic RAG**：动态迭代检索与推理
- ✅ **LLM 三层抽象**：High/Medium/Light 灵活切换，成本可控
- ✅ **极致轻量**：8GB 内存笔记本可运行，纯 CPU，无需 GPU
- ✅ **本地部署**：数据 100% 不出本地
- ✅ **混合检索**：BGE-M3 dense + sparse 检索
- ✅ **Web UI**：Streamlit 可视化界面

## 🚀 快速开始

### 1. 安装依赖

```bash
cd KnotKnot
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

**使用 OpenAI 格式 API：**

```env
# 配置所有层级使用 OpenAI 格式 API
LLM_HIGH_PROVIDER=openai
LLM_HIGH_MODEL=gpt-4
LLM_HIGH_TEMPERATURE=0.1
LLM_HIGH_MAX_TOKENS=4096

LLM_MEDIUM_PROVIDER=openai
LLM_MEDIUM_MODEL=gpt-4
LLM_MEDIUM_TEMPERATURE=0.3
LLM_MEDIUM_MAX_TOKENS=4096

LLM_LIGHT_PROVIDER=openai
LLM_LIGHT_MODEL=gpt-3.5-turbo
LLM_LIGHT_TEMPERATURE=0.5
LLM_LIGHT_MAX_TOKENS=2048

# API 配置
OPENAI_API_KEY=your-api-key-here
# 可选：自定义 API 端点（支持 Azure OpenAI、本地部署等）
# OPENAI_API_BASE=https://your-api-endpoint.com/v1
```

**或使用 Anthropic API：**

```env
ANTHROPIC_API_KEY=your-api-key-here
```

### 3. 初始化系统

```bash
python scripts/init_system.py
```

### 4. 启动 Web UI

```bash
streamlit run ui/app.py
```

访问 http://localhost:8501

## 📁 项目结构

```
KnotKnot/
├── src/
│   ├── agents/              # 智能体模块
│   │   ├── base_agent.py   # Agent 基类
│   │   └── planning_agent.py  # 规划 Agent
│   ├── llm/                 # LLM 抽象层
│   │   ├── factory.py      # LLM 工厂（三层抽象）
│   │   └── cost_tracker.py # 成本追踪
│   ├── retrieval/           # 检索模块
│   │   └── hybrid_search.py  # 混合检索
│   ├── storage/             # 存储层
│   │   └── chroma_client.py  # Chroma 客户端
│   └── utils/               # 工具类
│       ├── config.py       # 配置管理
│       └── logger.py       # 日志系统
├── ui/
│   └── app.py              # Streamlit Web UI
├── scripts/
│   └── init_system.py      # 系统初始化
├── data/                   # 数据目录
│   ├── documents/          # 原始文档
│   └── chroma_db/          # 向量数据库
├── logs/                   # 日志
├── docs/                   # 文档
├── requirements.txt        # 依赖清单
└── .env.example           # 环境变量模板
```

## 🎯 核心功能

### 当前实现（v0.2 - Agent System）

- ✅ LLM 三层抽象（High/Medium/Light）
- ✅ 成本追踪
- ✅ BGE-M3 混合检索
- ✅ Chroma 向量数据库
- ✅ Planning Agent（文档规划）
- ✅ Retrieval Agent（检索优化）
- ✅ Reasoning Agent（推理判断）
- ✅ Writing Agent（内容生成）
- ✅ Review Agent（质量审核）
- ✅ Agentic RAG 工作流（LangGraph）
- ✅ Web UI（完整界面）
- ✅ 配置管理
- ✅ 结构化日志
- ✅ OpenAI 格式 API 支持

### 待实现功能

- ⏳ 文档摄入模块（Docling 集成）
- ⏳ 文档导出（DOCX/PDF）
- ⏳ 语义缓存
- ⏳ 流式输出

## 🔧 配置说明

### LLM 配置

在 `.env` 中配置三层 LLM：

```env
# High 层（规划/推理/审核）- 顶级能力
LLM_HIGH_PROVIDER=anthropic
LLM_HIGH_MODEL=claude-opus-4-6

# Medium 层（内容撰写）- 性价比
LLM_MEDIUM_PROVIDER=anthropic
LLM_MEDIUM_MODEL=claude-sonnet-4-6

# Light 层（检索优化）- 低成本/本地
LLM_LIGHT_PROVIDER=ollama
LLM_LIGHT_MODEL=qwen3.5:32b
```

### 性能配置

```env
BATCH_SIZE=20          # 批处理大小
CHUNK_SIZE=512         # 分块大小
TOP_K=10              # 检索返回数量
MAX_WORKERS=4         # 最大并发数
```

## 📊 使用示例

### 1. 文档生成

1. 在 Web UI 的"文档生成"标签页
2. 输入需求描述
3. 选择文档类型
4. 点击"开始生成"
5. 系统自动执行：规划 → 检索 → 推理 → 撰写 → 审核
6. 下载生成的完整文档

### 2. 知识库管理

1. 在"知识库管理"标签页
2. 上传文档文件（PDF/DOCX/TXT/MD）
3. 系统自动索引到向量数据库

### 3. 检索测试

1. 在"检索测试"标签页
2. 输入查询内容
3. 查看检索结果和相似度

## 💰 成本估算

基于 v2.1 配置（High: Opus, Medium: Sonnet, Light: 本地）：

- 单文档（1万字）：$0.33-0.63
- 月度 100 篇：$33-63

## 📚 文档

- [方案文档](./Agentic%20RAG%20多智能体文档生成方案%20v2.1（重构版）.md) - 业务价值与核心特性
- [技术设计文档](./docs/技术设计文档.md) - 详细实现方案
- [部署运维文档](./docs/部署运维文档.md) - 部署与故障排查

## 🛠️ 开发

### 运行测试

```bash
pytest tests/
```

### 查看日志

```bash
tail -f logs/app.log
```

### 查看成本统计

在 Web UI 侧边栏查看实时成本统计

## 🔍 故障排查

### 问题：端口被占用

```bash
# 更换端口
streamlit run ui/app.py --server.port 8502
```

### 问题：内存不足

在 `.env` 中调整：

```env
BATCH_SIZE=10
CHUNK_SIZE=256
```

### 问题：API 调用失败

检查 API Key 是否正确配置：

```bash
echo $ANTHROPIC_API_KEY
```

## 📝 系统要求

- Python 3.10+
- 8GB RAM（推荐 16GB）
- 无需 GPU
- 稳定的网络连接（用于 API 调用）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Chroma](https://github.com/chroma-core/chroma)
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding)
- [Streamlit](https://streamlit.io/)
