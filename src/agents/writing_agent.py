"""Writing agent for document generation."""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier


class WritingAgent(BaseAgent):
    """Agent for writing document content."""

    def __init__(self):
        """Initialize writing agent with MEDIUM tier LLM."""
        super().__init__(tier=LLMTier.MEDIUM)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write content for current section.

        Input state:
            - sections: List of sections
            - current_section: Current section index
            - retrieved_docs: Retrieved documents
            - requirement: User requirement
            - outline: Document outline
            - content: Existing content

        Output state:
            - content: Updated content with new section
            - current_section: Incremented section index
        """
        sections = state.get("sections", [])
        current_section = state.get("current_section", 0)
        retrieved_docs = state.get("retrieved_docs", [])
        requirement = state.get("requirement", "")
        outline = state.get("outline", "")
        existing_content = state.get("content", "")

        if current_section >= len(sections):
            self.logger.info("writing_skipped", reason="no_more_sections")
            return state

        section = sections[current_section]

        self.logger.info(
            "writing_started",
            section=section,
            section_index=current_section
        )

        # Format retrieved documents
        docs_text = "\n\n".join([
            f"参考文档 {i+1}:\n{doc.get('text', doc.get('content', ''))}"
            for i, doc in enumerate(retrieved_docs[-10:])  # Last 10 docs
        ])

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的技术文档撰写专家。
根据大纲、参考文档和需求，撰写高质量的文档内容。

要求：
- 内容准确、逻辑清晰
- 结构完整、层次分明
- 语言专业、表达流畅
- 适当引用参考文档
- 使用 Markdown 格式"""),
            ("user", """需求：{requirement}

文档大纲：
{outline}

当前章节：{section}

参考文档：
{docs_text}

请撰写该章节内容。""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "requirement": requirement,
            "outline": outline,
            "section": section,
            "docs_text": docs_text if docs_text else "（暂无参考文档）"
        })

        section_content = response.content

        # Append to existing content
        new_content = existing_content + "\n\n" + section_content

        self.logger.info(
            "writing_completed",
            section=section,
            content_length=len(section_content)
        )

        return {
            **state,
            "content": new_content.strip(),
            "current_section": current_section + 1,
            "retrieved_docs": []  # Clear for next section
        }
