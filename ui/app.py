"""Streamlit Web UI for Agentic RAG Document Generator."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.logger import setup_logging, get_logger
from src.retrieval.hybrid_search import HybridSearcher
from src.workflow.graph import create_workflow
from src.llm.cost_tracker import CostTracker

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Agentic RAG 文档生成器",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'searcher' not in st.session_state:
    st.session_state.searcher = None
if 'workflow' not in st.session_state:
    st.session_state.workflow = None


def init_components():
    """Initialize components."""
    if st.session_state.searcher is None:
        with st.spinner("初始化检索系统..."):
            st.session_state.searcher = HybridSearcher()

    if st.session_state.workflow is None:
        with st.spinner("初始化 Agent 工作流..."):
            st.session_state.workflow = create_workflow()


# Main UI
st.title("📝 Agentic RAG 文档生成器 v2.1")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ 系统状态")

    # Initialize button
    if st.button("🔄 初始化系统", use_container_width=True):
        try:
            # Clear existing instances to force reload
            st.session_state.searcher = None
            st.session_state.workflow = None

            init_components()
            st.success("✅ 系统初始化成功！")
        except Exception as e:
            import traceback
            st.error(f"❌ 初始化失败: {e}")
            st.code(traceback.format_exc())
            logger.error("initialization_failed", error=str(e), exc_info=True)

    st.markdown("---")

    # Stats
    if st.session_state.searcher:
        stats = st.session_state.searcher.get_stats()
        st.metric("📚 文档数量", stats['document_count'])

    # Cost tracking
    st.markdown("---")
    st.subheader("💰 成本统计")
    cost_report = CostTracker.get_report()
    st.metric("总成本", f"${cost_report['total_cost']:.4f}")
    st.metric("API 调用次数", cost_report['total_calls'])

    if cost_report['by_tier']:
        st.markdown("**按层级：**")
        for tier, cost in cost_report['by_tier'].items():
            st.text(f"{tier}: ${cost:.4f}")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📄 文档生成", "📚 知识库管理", "🔍 检索测试"])

# Tab 1: Document Generation
with tab1:
    st.header("文档生成")

    col1, col2 = st.columns([2, 1])

    with col1:
        requirement = st.text_area(
            "需求描述",
            placeholder="请描述您需要生成的文档内容...",
            height=200
        )

    with col2:
        doc_type = st.selectbox(
            "文档类型",
            ["可行性研究报告", "初步设计文件", "技术方案", "项目总结", "其他"]
        )

        word_count = st.number_input(
            "目标字数",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000
        )

    if st.button("🚀 开始生成", type="primary", use_container_width=True):
        if not requirement:
            st.error("请输入需求描述！")
        elif not st.session_state.workflow:
            st.error("请先初始化系统！")
        else:
            try:
                # Initialize state
                initial_state = {
                    "requirement": requirement,
                    "doc_type": doc_type,
                    "outline": "",
                    "sections": [],
                    "current_section": 0,
                    "retrieved_docs": [],
                    "is_sufficient": False,
                    "reasoning": "",
                    "iteration_count": 0,
                    "content": "",
                    "final_content": "",
                    "review_feedback": "",
                    "last_query": ""
                }

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Agent execution log
                st.markdown("### 🤖 Agent 执行日志")
                log_container = st.container()
                agent_logs = []

                # Run workflow
                status_text.text("正在规划文档结构...")
                progress_bar.progress(10)

                result = None
                step_count = 0
                max_steps = 50  # Safety limit
                previous_state = {}

                for output in st.session_state.workflow.stream(initial_state):
                    step_count += 1
                    if step_count > max_steps:
                        st.warning("⚠️ 达到最大步骤限制，停止生成")
                        break

                    # Get the node name and state from output
                    # LangGraph stream returns dict with node name as key
                    node_name = list(output.keys())[0] if output else None
                    state = output.get(node_name, {}) if node_name else {}

                    # Log agent execution
                    if node_name == 'planning':
                        agent_logs.append({
                            'agent': '📋 Planning Agent',
                            'status': '完成',
                            'output': f"生成大纲，共 {len(state.get('sections', []))} 个章节\n\n大纲预览:\n{state.get('outline', '')[:200]}..."
                        })

                    elif node_name == 'retrieval':
                        agent_logs.append({
                            'agent': '🔍 Retrieval Agent',
                            'status': '完成',
                            'output': f"检索查询: {state.get('last_query', '')}\n检索到 {len(state.get('retrieved_docs', []))} 个文档"
                        })

                    elif node_name == 'reasoning':
                        is_sufficient = state.get('is_sufficient', False)
                        agent_logs.append({
                            'agent': '🧠 Reasoning Agent',
                            'status': '完成',
                            'output': f"信息评估: {'✅ 充分' if is_sufficient else '❌ 不足'}\n迭代次数: {state.get('iteration_count', 0)}\n\n推理:\n{state.get('reasoning', '')[:200]}..."
                        })

                    elif node_name == 'writing':
                        sections = state.get('sections', [])
                        current = state.get('current_section', 0)
                        agent_logs.append({
                            'agent': '✍️ Writing Agent',
                            'status': '完成',
                            'output': f"完成章节: {current}/{len(sections)}\n内容长度: {len(state.get('content', ''))} 字符\n\n内容预览:\n{state.get('content', '')[-200:]}"
                        })

                    elif node_name == 'review':
                        agent_logs.append({
                            'agent': '✅ Review Agent',
                            'status': '完成',
                            'output': f"审核完成\n最终文档长度: {len(state.get('final_content', ''))} 字符\n反馈: {state.get('review_feedback', '')}"
                        })

                    # Update log display
                    with log_container:
                        for i, log in enumerate(agent_logs[-10:]):  # Show last 10 logs
                            with st.expander(f"{log['agent']} - {log['status']}", expanded=(i >= len(agent_logs[-10:]) - 3)):
                                st.text(log['output'])

                    # Update progress based on current section
                    if 'current_section' in state and 'sections' in state:
                        sections = state.get('sections', [])
                        current = state.get('current_section', 0)
                        if len(sections) > 0:
                            progress = min(90, 10 + int(80 * current / len(sections)))
                            progress_bar.progress(progress)
                            status_text.text(f"正在处理章节 {current}/{len(sections)}...")

                    result = state
                    previous_state = state

                progress_bar.progress(100)
                status_text.text("生成完成！")

                if result and 'final_content' in result:
                    st.success("✅ 文档生成完成！")

                    # Display outline
                    if result.get('outline'):
                        st.markdown("### 📋 文档大纲")
                        st.markdown(result['outline'])

                    # Display final content
                    st.markdown("### 📄 生成的文档")
                    st.markdown(result['final_content'])

                    # Download button
                    st.download_button(
                        label="📥 下载文档",
                        data=result['final_content'],
                        file_name=f"{doc_type}_{requirement[:20]}.md",
                        mime="text/markdown"
                    )

                    # Display cost
                    cost_report = CostTracker.get_report()
                    st.info(f"💰 本次生成成本: ${cost_report['total_cost']:.4f}")

                else:
                    st.error("❌ 生成失败：未获得有效结果")

            except Exception as e:
                st.error(f"❌ 生成失败: {e}")
                logger.error("document_generation_failed", error=str(e), exc_info=True)

# Tab 2: Knowledge Base Management
with tab2:
    st.header("知识库管理")

    # Upload documents
    st.subheader("📤 上传文档")
    uploaded_files = st.file_uploader(
        "选择文档文件",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'md']
    )

    if uploaded_files and st.button("上传到知识库"):
        if not st.session_state.searcher:
            st.error("请先初始化系统！")
        else:
            with st.spinner(f"正在处理 {len(uploaded_files)} 个文件..."):
                try:
                    documents = []
                    metadatas = []

                    for file in uploaded_files:
                        content = file.read().decode('utf-8', errors='ignore')
                        documents.append(content)
                        metadatas.append({
                            'filename': file.name,
                            'size': len(content)
                        })

                    st.session_state.searcher.add_documents(
                        documents=documents,
                        metadatas=metadatas
                    )

                    st.success(f"✅ 成功上传 {len(uploaded_files)} 个文档！")

                except Exception as e:
                    st.error(f"❌ 上传失败: {e}")

    # Display stats
    st.markdown("---")
    st.subheader("📊 知识库统计")
    if st.session_state.searcher:
        stats = st.session_state.searcher.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("文档总数", stats['document_count'])
        with col2:
            st.metric("集合名称", stats['collection_name'])

# Tab 3: Retrieval Test
with tab3:
    st.header("检索测试")

    query = st.text_input("输入查询", placeholder="输入要检索的内容...")
    top_k = st.slider("返回结果数", 1, 20, 5)

    if st.button("🔍 执行检索"):
        if not query:
            st.error("请输入查询内容！")
        elif not st.session_state.searcher:
            st.error("请先初始化系统！")
        else:
            with st.spinner("正在检索..."):
                try:
                    results = st.session_state.searcher.search(
                        query=query,
                        top_k=top_k
                    )

                    st.success(f"✅ 找到 {len(results)} 条结果")

                    for i, result in enumerate(results, 1):
                        with st.expander(f"结果 {i} (距离: {result['distance']:.4f})"):
                            st.markdown(f"**ID:** {result['id']}")
                            st.markdown(f"**元数据:** {result['metadata']}")
                            st.markdown("**内容:**")
                            st.text(result['document'][:500] + "..." if len(result['document']) > 500 else result['document'])

                except Exception as e:
                    st.error(f"❌ 检索失败: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    Agentic RAG Document Generator v2.1 | Powered by Claude Opus 4.6
    </div>
    """,
    unsafe_allow_html=True
)
