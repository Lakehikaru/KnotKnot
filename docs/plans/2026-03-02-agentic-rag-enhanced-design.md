# Agentic RAG 增强型文档生成系统设计文档

> **设计版本**: v2.0 Enhanced
> **创建日期**: 2026-03-02
> **设计目标**: 基于 Agentic RAG 架构，通过迭代检索和质量评估机制提升文档生成质量

---

## 设计概述

本设计在 v2.0 Agentic RAG 方案基础上，重点增强了检索质量控制机制。核心创新是引入 **Retrieval ↔ Reasoning 迭代循环**，通过质量评估动态优化检索策略，显著提升素材检索的准确性和完整性。

### 核心设计理念

1. **智能体自主决策**：Reasoning Agent 评估检索质量，自主决定是否需要继续检索
2. **迭代优化**：支持多轮检索，每轮根据质量评估结果优化查询策略
3. **质量门控**：设置质量阈值，只有达标的素材才能进入写作阶段
4. **可控迭代**：限制最大迭代次数，避免无限循环

---

## 架构设计

### 系统架构图

```
用户需求输入
    ↓
┌─────────────────────────────────────────┐
│ Planning Agent (Claude Opus)            │
│ - 分析需求，生成文档大纲                 │
│ - 制定检索策略（查询、阈值、迭代次数）    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Retrieval Agent (Qdrant + bge-small)   │
│ - 执行混合搜索（向量+关键词+元数据）     │
│ - 支持查询优化（根据 refinement hints） │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Reasoning Agent (Claude Opus)           │
│ - 评估检索质量（相关性、完整性、可信度）  │
│ - 检测信息缺口                          │
│ - 生成优化建议                          │
│ - 决策：继续检索 or 进入写作             │
└─────────────────────────────────────────┘
    ↓
质量达标？
├─ 否 → 返回 Retrieval Agent（优化查询）
└─ 是 → 继续
         ↓
    ┌─────────────────────────────────────────┐
    │ Writing Agent (GPT-4o)                  │
    │ - 基于检索素材生成章节内容               │
    │ - 保持引用来源                          │
    └─────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────┐
    │ Review Agent (Claude Opus)              │
    │ - 事实核查、逻辑一致性检查               │
    │ - 格式规范性验证                        │
    └─────────────────────────────────────────┘
         ↓
    通过？
    ├─ 否 → 返回 Writing Agent（重写）
    └─ 是 → 继续
             ↓
        ┌─────────────────────────────────────────┐
        │ Editor Agent (GPT-4o)                   │
        │ - 最终润色和格式化                       │
        └─────────────────────────────────────────┘
             ↓
        输出最终文档
```

### 智能体职责划分

| 智能体 | 模型 | 核心职责 | 输入 | 输出 |
|--------|------|---------|------|------|
| **Planning Agent** | Claude Opus 4.6 | 需求分析、大纲规划、检索策略制定 | 用户需求、文档类型 | 文档大纲、检索策略（查询、阈值、迭代次数） |
| **Retrieval Agent** | Qdrant + bge-small-zh | 执行混合搜索、查询优化 | 查询文本、过滤条件、优化建议 | 检索结果集（文档+元数据+相关度分数） |
| **Reasoning Agent** | Claude Opus 4.6 | 质量评估、信息缺口检测、优化建议生成 | 章节需求、检索结果 | 质量分数、缺口列表、优化建议、决策（继续/停止） |
| **Writing Agent** | GPT-4o | 内容生成、引用标注 | 章节要求、检索素材 | 章节内容（带引用） |
| **Review Agent** | Claude Opus 4.6 | 质量审核、事实核查 | 完整文档、原始需求 | 审核结果（通过/不通过）、问题列表、改进建议 |
| **Editor Agent** | GPT-4o | 最终润色、格式统一 | 文档内容、审核建议 | 最终文档 |

---

## 核心创新：迭代检索机制

### 工作流程

```
第1轮检索：
  Retrieval Agent: 使用初始查询 → 返回结果集A
  Reasoning Agent: 评估质量 = 0.65（低于阈值0.7）
  决策: 继续检索
  生成优化建议: ["添加关键词：成本预算", "过滤文档类型：财务报表"]

第2轮检索：
  Retrieval Agent: 优化查询 = "项目背景 成本预算" + 过滤(财务报表) → 返回结果集B
  Reasoning Agent: 评估质量 = 0.75（达到阈值）
  决策: 进入写作

Writing Agent: 基于结果集A+B生成内容
```

### 质量评估维度

**Reasoning Agent 评估三个维度**：

1. **相关性（Relevance）**：检索到的文档与章节需求的匹配度
   - 评分标准：关键词覆盖率、语义相似度
   - 权重：33%

2. **完整性（Completeness）**：是否覆盖了所有必要信息
   - 评分标准：信息缺口数量、关键要素覆盖率
   - 权重：33%

3. **可信度（Credibility）**：文档来源的可靠性
   - 评分标准：文档类型、发布时间、作者权威性
   - 权重：34%

**综合质量分数** = (相关性 + 完整性 + 可信度) / 3

### 决策逻辑

```python
def should_continue_retrieval(state):
    quality = state['quality_assessment']['quality_score']
    iteration = state['retrieval_iteration']
    threshold = state['retrieval_strategy']['quality_threshold']
    max_iterations = state['retrieval_strategy']['max_iterations']

    # 条件1：质量达标 → 停止检索
    if quality >= threshold:
        return "writing"

    # 条件2：达到最大迭代次数 → 强制停止
    if iteration >= max_iterations:
        return "writing"

    # 条件3：Reasoning Agent 建议继续 → 继续检索
    if state['refinement_hints']['action'] == "refine_query":
        return "retrieval"

    return "writing"
```

### 查询优化策略

**Retrieval Agent 根据 Reasoning Agent 的建议优化查询**：

1. **添加关键词**：补充缺失的关键信息
   - 示例：原查询 "项目背景" → 优化后 "项目背景 成本预算 技术方案"

2. **调整过滤条件**：缩小或扩大搜索范围
   - 示例：添加过滤 `document_type: "财务报表"`

3. **改变查询策略**：调整向量搜索和关键词搜索的权重
   - 示例：提高关键词搜索权重以获得更精确的匹配

4. **扩展语义范围**：使用同义词或相关概念
   - 示例：原查询 "成本" → 优化后 "成本 预算 费用 投资"

---

## 状态管理

### DocumentState 定义

```python
class DocumentState(TypedDict):
    # 用户输入
    requirements: str              # 用户需求描述
    document_type: str             # "可研文件" | "初设文件" | "投标文件"

    # Planning Agent 输出
    outline: Dict[str, Any]        # 文档大纲
    retrieval_strategy: Dict       # 检索策略配置

    # Retrieval 状态
    current_section_id: str        # 当前处理的章节ID
    retrieval_iteration: int       # 当前迭代次数（0开始）
    retrieval_history: List[Dict]  # 检索历史记录
    retrieved_docs: List[Dict]     # 累积的检索结果

    # Reasoning Agent 输出
    quality_assessment: Dict       # 质量评估结果
    information_gaps: List[str]    # 信息缺口列表
    refinement_hints: Dict         # 优化建议

    # Writing Agent 输出
    sections_content: Dict[str, str]  # section_id -> content

    # Review Agent 输出
    review_result: Dict            # 审核结果
    review_retry_count: int        # 审核重试次数

    # 最终输出
    final_document: str            # 最终文档

    # 系统资源
    retriever: Any                 # Qdrant 检索器实例
```

### 状态流转

```
初始状态:
  requirements: "生成可研报告..."
  document_type: "可研文件"
  retrieval_iteration: 0
  retrieved_docs: []

↓ Planning Agent

  outline: {...}
  retrieval_strategy: {
    queries: [{
      section_id: "1",
      initial_query: "项目背景",
      quality_threshold: 0.7,
      max_iterations: 3
    }]
  }

↓ Retrieval Agent (第1轮)

  retrieval_iteration: 1
  retrieved_docs: [doc1, doc2, doc3]
  retrieval_history: [{iteration: 0, query: "项目背景", results_count: 3}]

↓ Reasoning Agent

  quality_assessment: {quality_score: 0.65, ...}
  information_gaps: ["缺少成本数据"]
  refinement_hints: {action: "refine_query", suggestions: ["添加关键词：成本"]}

↓ 决策: 继续检索

↓ Retrieval Agent (第2轮)

  retrieval_iteration: 2
  retrieved_docs: [doc1, doc2, doc3, doc4, doc5]  # 累积
  retrieval_history: [{...}, {iteration: 1, query: "项目背景 成本", results_count: 2}]

↓ Reasoning Agent

  quality_assessment: {quality_score: 0.75, ...}
  refinement_hints: {action: "continue_writing"}

↓ 决策: 进入写作

↓ Writing Agent

  sections_content: {"1": "第一章内容...", "2": "第二章内容..."}

↓ Review Agent

  review_result: {approved: true, overall_score: 0.85, ...}

↓ 决策: 进入编辑

↓ Editor Agent

  final_document: "完整的最终文档..."
```

---

## LangGraph 实现

### 状态图结构

```python
workflow = StateGraph(DocumentState)

# 添加节点
workflow.add_node("planner", planning_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("reasoning", reasoning_node)
workflow.add_node("writer", writing_node)
workflow.add_node("reviewer", review_node)
workflow.add_node("editor", editor_node)

# 线性流程
workflow.set_entry_point("planner")
workflow.add_edge("planner", "retrieval")
workflow.add_edge("retrieval", "reasoning")

# 关键：迭代检索循环
workflow.add_conditional_edges(
    "reasoning",
    should_continue_retrieval,
    {
        "retrieval": "retrieval",  # 循环回去
        "writing": "writer"         # 继续前进
    }
)

workflow.add_edge("writer", "reviewer")

# 审核循环
workflow.add_conditional_edges(
    "reviewer",
    should_continue_review,
    {
        "writer": "writer",  # 循环回去
        "editor": "editor"   # 继续前进
    }
)

workflow.add_edge("editor", END)

app = workflow.compile()
```

### 关键节点实现

**Reasoning Node（核心）**：

```python
def reasoning_node(state: DocumentState) -> DocumentState:
    """评估检索质量，决定下一步行动"""

    reasoning_agent = ReasoningAgent()

    # 获取当前章节需求
    section = state['outline']['sections'][0]

    # 评估检索结果
    assessment = reasoning_agent.evaluate(
        section_requirements=section['content_requirements'],
        retrieved_docs=state['retrieved_docs']
    )

    # 更新状态
    return {
        **state,
        "quality_assessment": assessment,
        "information_gaps": assessment['gaps'],
        "refinement_hints": assessment['refinement_hints']
    }
```

**Retrieval Node（支持优化）**：

```python
def retrieval_node(state: DocumentState) -> DocumentState:
    """执行检索，支持查询优化"""

    retrieval_agent = RetrievalAgent(state['retriever'])
    strategy = state['retrieval_strategy']['queries'][0]

    # 第一次检索：使用初始查询
    if state['retrieval_iteration'] == 0:
        query = strategy['initial_query']
        hints = []
    else:
        # 后续检索：使用优化建议
        query = strategy['initial_query']
        hints = state['refinement_hints']['suggestions']

    # 执行检索
    results = retrieval_agent.retrieve(
        query=query,
        filters={"document_type": strategy.get('doc_type_filter')},
        refinement_hints=hints
    )

    # 合并结果（去重）
    existing_ids = {doc['id'] for doc in state.get('retrieved_docs', [])}
    new_docs = [doc for doc in results if doc['id'] not in existing_ids]

    return {
        **state,
        "retrieved_docs": state.get('retrieved_docs', []) + new_docs,
        "retrieval_iteration": state['retrieval_iteration'] + 1,
        "retrieval_history": state.get('retrieval_history', []) + [{
            "iteration": state['retrieval_iteration'],
            "query": query,
            "hints": hints,
            "results_count": len(new_docs)
        }]
    }
```

---

## 技术选型理由

### 为什么选择 Claude Opus 做 Planning 和 Reasoning？

1. **强大的推理能力**：需要深度分析需求、评估质量、生成优化建议
2. **结构化输出**：擅长生成 JSON 格式的结构化数据
3. **调用次数少**：Planning 和 Reasoning 每个文档只调用 3-5 次，成本可控

### 为什么选择 GPT-4o 做 Writing？

1. **成本优势**：Writing Agent 调用频繁（每章节1次），GPT-4o 成本仅为 Opus 的 1/6
2. **生成质量**：内容生成质量足够好，性价比高
3. **速度快**：响应速度快，提升用户体验

### 为什么使用 LangGraph 而不是 AutoGen？

1. **AutoGen 已废弃**：2025年10月官方宣布停止维护
2. **LangGraph 是主流**：2026年生产环境首选，社区活跃
3. **状态图清晰**：显式定义状态转换，易于调试和维护
4. **条件路由强大**：原生支持复杂的条件分支和循环

---

## 性能优化策略

### 1. 缓存机制

**问题**：重复检索相同查询浪费 API 调用

**解决**：
```python
# 检索结果缓存
retrieval_cache = {}

def retrieve_with_cache(query, filters):
    cache_key = f"{query}_{json.dumps(filters)}"

    if cache_key in retrieval_cache:
        return retrieval_cache[cache_key]

    results = retriever.search(query, filters)
    retrieval_cache[cache_key] = results
    return results
```

### 2. 批量处理

**问题**：逐章节生成效率低

**解决**：
```python
# 并行生成多个章节
from concurrent.futures import ThreadPoolExecutor

def write_sections_parallel(sections, retrieved_docs):
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(writer.write_section, section, retrieved_docs)
            for section in sections
        ]
        return [f.result() for f in futures]
```

### 3. 早停机制

**问题**：质量已经很高但还在继续迭代

**解决**：
```python
# 如果质量分数 > 0.9，直接停止（即使未达到 max_iterations）
if quality_score > 0.9:
    return "writing"
```

---

## 成本优化

### API 调用成本分析

**单次文档生成（1万字，5个章节）**：

| 智能体 | 模型 | 调用次数 | 单次成本 | 小计 |
|--------|------|---------|---------|------|
| Planning | Claude Opus | 1 | $0.10 | $0.10 |
| Retrieval | 本地嵌入 | 3-9 | $0 | $0 |
| Reasoning | Claude Opus | 3-9 | $0.05 | $0.15-0.45 |
| Writing | GPT-4o | 5 | $0.03 | $0.15 |
| Review | Claude Opus | 1 | $0.10 | $0.10 |
| Editor | GPT-4o | 1 | $0.03 | $0.03 |
| **总计** | - | - | - | **$0.53-0.83** |

**月度成本（100篇文档）**：$53-83

### 成本优化建议

1. **调整迭代次数**：将 `max_iterations` 从 3 降到 2，节省 30% Reasoning 成本
2. **提高阈值**：将 `quality_threshold` 从 0.7 提到 0.75，减少不必要的迭代
3. **使用本地 LLM**：对于简单文档，可以用本地 Llama 3 替代 GPT-4o

---

## 风险与缓解

### 风险1：无限循环

**描述**：Reasoning Agent 一直认为质量不够，导致无限迭代

**缓解措施**：
- 设置 `max_iterations` 硬限制（默认3次）
- 添加质量下降检测：如果连续2轮质量分数下降，强制停止

### 风险2：API 调用失败

**描述**：网络问题或 API 限流导致调用失败

**缓解措施**：
```python
# 添加重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_llm_with_retry(prompt):
    return llm.invoke(prompt)
```

### 风险3：检索质量评估不准确

**描述**：Reasoning Agent 误判检索质量

**缓解措施**：
- 提供详细的评估 Prompt，包含评分标准和示例
- 人工抽查评估结果，持续优化 Prompt
- 添加人工介入点：质量分数在 0.6-0.7 之间时，询问用户是否继续

---

## 测试策略

### 单元测试

```python
# 测试 Reasoning Agent 的质量评估
def test_reasoning_agent_evaluation():
    agent = ReasoningAgent()

    # 高质量文档
    high_quality_docs = [...]
    result = agent.evaluate("项目背景", high_quality_docs)
    assert result['quality_score'] > 0.8

    # 低质量文档
    low_quality_docs = [...]
    result = agent.evaluate("项目背景", low_quality_docs)
    assert result['quality_score'] < 0.5
    assert result['refinement_hints']['action'] == "refine_query"
```

### 集成测试

```python
# 测试完整工作流
def test_full_workflow():
    workflow = build_workflow(retriever)

    result = workflow.invoke({
        "requirements": "生成智慧城市可研报告",
        "document_type": "可研文件"
    })

    # 验证迭代检索发生
    assert result['retrieval_iteration'] > 1

    # 验证最终质量
    assert result['quality_assessment']['quality_score'] >= 0.7

    # 验证文档生成
    assert len(result['final_document']) > 5000
```

### 性能测试

```python
# 测试生成速度
import time

def test_generation_speed():
    start = time.time()

    result = workflow.invoke({...})

    duration = time.time() - start
    assert duration < 600  # 10分钟内完成
```

---

## 部署建议

### 开发环境

```bash
# 本地开发
- Qdrant: Docker 本地运行
- 嵌入模型: GPU 加速（RTX 4060 Ti）
- UI: Streamlit 本地运行（localhost:8501）
```

### 生产环境（小组内部）

```bash
# 工作站部署
- 硬件: 32GB RAM + RTX 4060 Ti
- Qdrant: Docker 持久化存储
- UI: Streamlit + Nginx 反向代理
- 访问: 内网 IP（如 192.168.1.100:8501）
```

### 监控指标

1. **性能指标**：
   - 平均生成时间
   - API 调用次数
   - 检索迭代次数分布

2. **质量指标**：
   - 平均质量分数
   - 审核通过率
   - 用户满意度

3. **成本指标**：
   - 每日 API 成本
   - 单文档平均成本

---

## 后续优化方向

### 短期（1-2个月）

1. **Prompt 优化**：持续优化各智能体的 Prompt，提升生成质量
2. **模板系统**：添加更多文档模板（技术方案、商务标书等）
3. **用户反馈**：添加用户评分和反馈收集

### 中期（3-6个月）

1. **多模态支持**：支持图表、表格的智能生成
2. **协作功能**：支持多人协作编辑文档
3. **版本管理**：文档版本控制和历史记录

### 长期（6-12个月）

1. **知识图谱**：构建领域知识图谱，提升检索准确性
2. **自动学习**：根据用户反馈自动优化检索策略
3. **本地 LLM**：部署本地大模型，降低 API 依赖

---

## 总结

本设计通过引入 **Retrieval ↔ Reasoning 迭代循环机制**，显著提升了文档生成系统的检索质量和内容准确性。核心优势包括：

1. ✅ **智能质量控制**：Reasoning Agent 自主评估和决策
2. ✅ **动态优化**：根据质量评估动态调整检索策略
3. ✅ **可控迭代**：通过阈值和最大迭代次数避免无限循环
4. ✅ **成本优化**：混合使用 Claude Opus 和 GPT-4o，平衡质量和成本
5. ✅ **架构简洁**：统一的 Agentic RAG 框架，易于维护和扩展

相比 v1.0 方案（Kotaemon + LangGraph），本方案在开发周期、代码复杂度、检索准确率、API 成本等方面都有显著优势，特别适合小组内部使用场景。

---

**设计文档结束**
