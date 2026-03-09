"""Reasoning agent for document generation."""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier


class ReasoningAgent(BaseAgent):
    """Agent for reasoning about retrieved information."""

    def __init__(self):
        """Initialize reasoning agent with HIGH tier LLM."""
        super().__init__(tier=LLMTier.HIGH)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if retrieved information is sufficient.

        Input state:
            - sections: List of sections
            - current_section: Current section index
            - retrieved_docs: Retrieved documents
            - requirement: User requirement
            - iteration_count: Current iteration count

        Output state:
            - is_sufficient: Whether information is sufficient
            - reasoning: Reasoning explanation
            - iteration_count: Updated iteration count
        """
        sections = state.get("sections", [])
        current_section = state.get("current_section", 0)
        retrieved_docs = state.get("retrieved_docs", [])
        requirement = state.get("requirement", "")
        iteration_count = state.get("iteration_count", 0)

        if current_section >= len(sections):
            return {
                **state,
                "is_sufficient": True,
                "reasoning": "All sections completed"
            }

        section = sections[current_section]

        self.logger.info(
            "reasoning_started",
            section=section,
            docs_count=len(retrieved_docs),
            iteration=iteration_count
        )

        # Format retrieved documents
        docs_text = "\n\n".join([
            f"文档 {i+1}:\n{doc.get('text', doc.get('content', ''))}"
            for i, doc in enumerate(retrieved_docs[-5:])  # Last 5 docs
        ])

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个信息充分性判断专家。
分析检索到的文档是否足够撰写当前章节。

输出格式（JSON）：
{
  "is_sufficient": true/false,
  "reasoning": "判断理由",
  "missing_info": "缺失的信息（如果不充分）"
}"""),
            ("user", """需求：{requirement}

当前章节：{section}

已检索文档：
{docs_text}

当前迭代次数：{iteration_count}/5

请判断信息是否充分。""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "requirement": requirement,
            "section": section,
            "docs_text": docs_text if docs_text else "（暂无文档）",
            "iteration_count": iteration_count
        })

        # Parse response
        import json
        try:
            result = json.loads(response.content)
            is_sufficient = result.get("is_sufficient", False)
            reasoning = result.get("reasoning", "")
        except:
            # Fallback: simple text parsing
            content = response.content.lower()
            is_sufficient = "true" in content or "充分" in content
            reasoning = response.content

        # Force sufficient if max iterations reached
        if iteration_count >= 4:
            is_sufficient = True
            reasoning += " (达到最大迭代次数)"

        self.logger.info(
            "reasoning_completed",
            is_sufficient=is_sufficient,
            iteration=iteration_count
        )

        return {
            **state,
            "is_sufficient": is_sufficient,
            "reasoning": reasoning,
            "iteration_count": iteration_count + 1
        }
