"""Cost tracking for LLM API calls."""

from typing import Dict, List
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CostTracker:
    """Track LLM API call costs."""

    # Pricing per 1M tokens (USD)
    PRICING = {
        "claude-opus-4-6": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5": {"input": 0.8, "output": 4.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    }

    _records: List[Dict] = []

    @classmethod
    def track(
        cls,
        agent: str,
        tier: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """
        Track a single LLM API call.

        Args:
            agent: Agent name
            tier: LLM tier (high/medium/light)
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
        """
        pricing = cls.PRICING.get(model, {"input": 0, "output": 0})

        cost = (
            input_tokens / 1_000_000 * pricing["input"] +
            output_tokens / 1_000_000 * pricing["output"]
        )

        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "tier": tier,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }

        cls._records.append(record)

        logger.info(
            "llm_call_tracked",
            agent=agent,
            tier=tier,
            model=model,
            cost=f"${cost:.4f}"
        )

    @classmethod
    def get_report(cls) -> Dict:
        """
        Generate cost report.

        Returns:
            Dict with total cost, cost by tier, and call count
        """
        if not cls._records:
            return {
                "total_cost": 0.0,
                "by_tier": {},
                "by_agent": {},
                "total_calls": 0
            }

        total_cost = sum(r["cost"] for r in cls._records)

        by_tier = {}
        for record in cls._records:
            tier = record["tier"]
            by_tier[tier] = by_tier.get(tier, 0) + record["cost"]

        by_agent = {}
        for record in cls._records:
            agent = record["agent"]
            by_agent[agent] = by_agent.get(agent, 0) + record["cost"]

        return {
            "total_cost": total_cost,
            "by_tier": by_tier,
            "by_agent": by_agent,
            "total_calls": len(cls._records)
        }

    @classmethod
    def reset(cls):
        """Reset all tracking records."""
        cls._records = []
        logger.info("cost_tracker_reset")
