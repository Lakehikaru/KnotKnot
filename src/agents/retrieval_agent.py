"""Retrieval agent for document generation."""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
import requests
from bs4 import BeautifulSoup

from src.agents.base_agent import BaseAgent
from src.llm.factory import LLMTier
from src.storage.chroma_client import ChromaClient
from src.retrieval.hybrid_search import HybridSearcher
from src.utils.config import settings


class RetrievalAgent(BaseAgent):
    """Agent for retrieving relevant documents."""

    def __init__(self):
        """Initialize retrieval agent with LIGHT tier LLM."""
        super().__init__(tier=LLMTier.LIGHT)
        self.chroma = ChromaClient()
        self.searcher = HybridSearcher()
        self.relevance_threshold = 0.6  # 相关性阈值
        self.max_web_results = 3  # 最多联网搜索结果数

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

        # Handle both string and list responses (OpenAI compatibility)
        if isinstance(response.content, list):
            query = response.content[0].get("text", "") if response.content else ""
        else:
            query = response.content
        query = query.strip()

        self.logger.info("query_generated", query=query)

        # Perform hybrid search
        try:
            # Step 1: 本地检索
            local_results = self.searcher.search(query, top_k=5)

            # 计算本地结果的平均相关性
            avg_relevance = 0
            if local_results:
                avg_relevance = sum(doc.get("score", 0) for doc in local_results) / len(local_results)

            self.logger.info(
                "local_retrieval_completed",
                results_count=len(local_results),
                avg_relevance=avg_relevance
            )

            # Step 2: 如果本地结果不足或相关性低，触发联网搜索
            web_results = []
            if len(local_results) < 3 or avg_relevance < self.relevance_threshold:
                self.logger.info("triggering_web_search", reason="insufficient_local_results")
                web_results = self._web_search(query)
                self.logger.info("web_search_completed", results_count=len(web_results))

            # Step 3: 合并结果
            all_results = local_results + web_results

            retrieved_docs = state.get("retrieved_docs", [])
            retrieved_docs.extend(all_results)

            self.logger.info(
                "retrieval_completed",
                local_count=len(local_results),
                web_count=len(web_results),
                total_count=len(all_results)
            )

            return {
                **state,
                "retrieved_docs": retrieved_docs,
                "last_query": query,
                "has_sufficient_context": len(all_results) >= 3
            }

        except Exception as e:
            self.logger.error("retrieval_failed", error=str(e))
            # Return state unchanged on error
            return state

    def _web_search(self, query: str) -> List[Dict[str, Any]]:
        """
        使用 DuckDuckGo 进行联网搜索（无需 API Key）

        Args:
            query: 搜索查询

        Returns:
            搜索结果列表
        """
        results = []
        try:
            # 使用 DuckDuckGo HTML 搜索（无需 API）
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.post(url, data=params, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.find_all('div', class_='result', limit=self.max_web_results)

                for item in search_results:
                    title_elem = item.find('a', class_='result__a')
                    snippet_elem = item.find('a', class_='result__snippet')

                    if title_elem and snippet_elem:
                        results.append({
                            "content": f"{title_elem.get_text(strip=True)}\n{snippet_elem.get_text(strip=True)}",
                            "source": "web",
                            "url": title_elem.get('href', ''),
                            "score": 0.5  # 网络结果默认中等相关性
                        })

            self.logger.info("web_search_success", results_count=len(results))

        except Exception as e:
            self.logger.warning("web_search_failed", error=str(e))

        return results
