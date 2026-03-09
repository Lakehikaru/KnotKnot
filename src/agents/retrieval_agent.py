"""Retrieval agent for document generation."""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier
from src.storage.chroma_client import ChromaClient
from src.retrieval.hybrid_search import HybridSearcher


class RetrievalAgent(BaseAgent):
    """Agent for retrieving relevant documents."""

    def __init__(self):
        """Initialize retrieval agent with LIGHT tier LLM."""
        super().__init__(tier=LLMTier.LIGHT)
        self.chroma = ChromaClient()
        self.searcher = HybridSearcher()

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents based on current section.

        Input state:
            - sections: List of sections
            - current_section: Current section index
            - requirement: User requirement
            - retrieved_docs: Previously retrieved documents

        Output state:
            - retrieved_docs: Updated list of retrieved documents
        """
        sections = state.get("sections", [])
        current_section = state.get("current_section", 0)
        requirement = state.get("requirement", "")

        if current_section >= len(sections):
            self.logger.info("retrieval_skipped", reason="no_more_sections")
            return state

        section = sections[current_section]

        self.logger.info(
            "retrieval_started",
            section=section,
            section_index=current_section
        )

        # Generate search query using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个检索查询优化专家。
根据文档章节和需求，生成最优的检索查询。

输出格式：
直接输出查询关键词，不要其他内容。"""),
            ("user", """需求：{requirement}

当前章节：{section}

请生成检索查询。""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "requirement": requirement,
            "section": section
        })

        query = response.content.strip()

        self.logger.info("query_generated", query=query)

        # Perform hybrid search
        try:
            results = self.searcher.search(query, top_k=5)

            retrieved_docs = state.get("retrieved_docs", [])
            retrieved_docs.extend(results)

            self.logger.info(
                "retrieval_completed",
                results_count=len(results)
            )

            return {
                **state,
                "retrieved_docs": retrieved_docs,
                "last_query": query
            }

        except Exception as e:
            self.logger.error("retrieval_failed", error=str(e))
            # Return state unchanged on error
            return state
