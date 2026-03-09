"""Base agent class for all agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from src.llm.factory import LLMFactory, LLMTier
from src.llm.cost_tracker import CostTracker
from src.utils.logger import get_logger


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, tier: LLMTier):
        """
        Initialize agent.

        Args:
            tier: LLM tier to use (high/medium/light)
        """
        self.tier = tier
        self.llm = LLMFactory.get_llm(tier)
        self.logger = get_logger(self.__class__.__name__)

        self.logger.info(
            "agent_initialized",
            agent=self.__class__.__name__,
            tier=tier
        )

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.

        Args:
            state: Current state dictionary

        Returns:
            Updated state dictionary
        """
        pass

    def _track_cost(self, input_tokens: int, output_tokens: int, model: str):
        """
        Track LLM API call cost.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
        """
        CostTracker.track(
            agent=self.__class__.__name__,
            tier=self.tier.value,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
