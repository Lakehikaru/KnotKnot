"""LangGraph workflow for Agentic RAG document generation."""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from src.agents.planning_agent import PlanningAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.writing_agent import WritingAgent
from src.agents.review_agent import ReviewAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State shared across all agents."""
    requirement: str
    doc_type: str
    outline: str
    sections: List[str]
    current_section: int
    retrieved_docs: List[Dict]
    is_sufficient: bool
    reasoning: str
    iteration_count: int
    content: str
    final_content: str
    review_feedback: str
    last_query: str


def create_workflow():
    """Create the Agentic RAG workflow."""

    # Initialize agents
    planning_agent = PlanningAgent()
    retrieval_agent = RetrievalAgent()
    reasoning_agent = ReasoningAgent()
    writing_agent = WritingAgent()
    review_agent = ReviewAgent()

    # Create workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planning", planning_agent.run)
    workflow.add_node("retrieval", retrieval_agent.run)
    workflow.add_node("reasoning", reasoning_agent.run)
    workflow.add_node("writing", writing_agent.run)
    workflow.add_node("review", review_agent.run)

    # Define edges
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "retrieval")
    workflow.add_edge("retrieval", "reasoning")

    # Conditional edge: continue retrieval or proceed to writing
    workflow.add_conditional_edges(
        "reasoning",
        should_continue_retrieval,
        {
            "continue": "retrieval",
            "proceed": "writing"
        }
    )

    # Conditional edge: write next section or review
    workflow.add_conditional_edges(
        "writing",
        should_continue_writing,
        {
            "continue": "retrieval",
            "review": "review"
        }
    )

    workflow.add_edge("review", END)

    logger.info("workflow_created")

    return workflow.compile()


def should_continue_retrieval(state: AgentState) -> str:
    """Determine if retrieval should continue."""
    iteration_count = state.get("iteration_count", 0)
    is_sufficient = state.get("is_sufficient", False)

    # Max 5 iterations per section
    if iteration_count >= 5:
        logger.info("retrieval_stopped", reason="max_iterations")
        return "proceed"

    if is_sufficient:
        logger.info("retrieval_stopped", reason="sufficient_info")
        return "proceed"
    else:
        logger.info("retrieval_continuing", iteration=iteration_count)
        return "continue"


def should_continue_writing(state: AgentState) -> str:
    """Determine if writing should continue to next section."""
    sections = state.get("sections", [])
    current_section = state.get("current_section", 0)

    if current_section >= len(sections):
        logger.info("writing_completed", total_sections=len(sections))
        return "review"
    else:
        logger.info(
            "writing_continuing",
            current=current_section,
            total=len(sections)
        )
        # Reset iteration count for next section
        state["iteration_count"] = 0
        return "continue"
