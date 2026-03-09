"""Planning agent for document generation."""

from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier


class PlanningAgent(BaseAgent):
    """Agent for planning document structure."""

    def __init__(self):
        """Initialize planning agent with HIGH tier LLM."""
        super().__init__(tier=LLMTier.HIGH)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate document outline based on requirements.

        Input state:
            - requirement: User requirement description
            - doc_type: Document type

        Output state:
            - outline: Document outline
            - sections: List of sections
        """
        requirement = state.get("requirement", "")
        doc_type = state.get("doc_type", "")

        self.logger.info(
            "planning_started",
            doc_type=doc_type,
            requirement_length=len(requirement)
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的文档规划专家。
根据用户需求，生成详细的文档大纲。

输出格式：
1. 文档标题
2. 各章节标题与内容要点
3. 预估字数

要求：
- 结构清晰、逻辑严密
- 章节划分合理
- 内容要点具体"""),
            ("user", """需求：{requirement}

文档类型：{doc_type}

请生成文档大纲。""")
        ])

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "requirement": requirement,
            "doc_type": doc_type
        })

        outline = response.content

        # Parse outline into sections (simple split by lines)
        sections = [
            line.strip()
            for line in outline.split('\n')
            if line.strip() and (line.strip().startswith('#') or line.strip()[0].isdigit())
        ]

        self.logger.info(
            "planning_completed",
            sections_count=len(sections)
        )

        # Update state
        return {
            **state,
            "outline": outline,
            "sections": sections,
            "current_section": 0
        }
