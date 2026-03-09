"""Review agent for document generation."""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier


class ReviewAgent(BaseAgent):
    """Agent for reviewing and improving document content."""

    def __init__(self):
        """Initialize review agent with HIGH tier LLM."""
        super().__init__(tier=LLMTier.HIGH)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review and improve document content.

        Input state:
            - content: Document content
            - requirement: User requirement
            - outline: Document outline

        Output state:
            - final_content: Reviewed and improved content
            - review_feedback: Review feedback
        """
        content = state.get("content", "")
        requirement = state.get("requirement", "")
        outline = state.get("outline", "")

        self.logger.info(
            "review_started",
            content_length=len(content)
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档审核专家。
审核文档内容，提出改进建议并优化内容。

审核要点：
1. 内容完整性：是否覆盖所有要点
2. 逻辑连贯性：章节间是否衔接自然
3. 准确性：信息是否准确无误
4. 可读性：表达是否清晰易懂
5. 格式规范：Markdown 格式是否正确

输出格式：
1. 改进后的完整文档内容
2. 审核意见（在文档末尾用注释标注）"""),
            ("user", """需求：{requirement}

原始大纲：
{outline}

文档内容：
{content}

请审核并改进文档。""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "requirement": requirement,
            "outline": outline,
            "content": content
        })

        final_content = response.content

        self.logger.info(
            "review_completed",
            final_length=len(final_content)
        )

        return {
            **state,
            "final_content": final_content,
            "review_feedback": "审核完成"
        }
