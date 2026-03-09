"""LLM Factory - Three-tier abstraction for LLM providers."""

from enum import Enum
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMTier(str, Enum):
    """LLM tier levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LIGHT = "light"


class LLMFactory:
    """Factory for creating LLM instances with three-tier abstraction."""

    @classmethod
    def _get_config(cls, tier: LLMTier) -> dict:
        """Get configuration for a specific tier."""
        if tier == LLMTier.HIGH:
            return {
                "provider": settings.llm_high_provider,
                "model": settings.llm_high_model,
                "temperature": settings.llm_high_temperature,
                "max_tokens": settings.llm_high_max_tokens,
            }
        elif tier == LLMTier.MEDIUM:
            return {
                "provider": settings.llm_medium_provider,
                "model": settings.llm_medium_model,
                "temperature": settings.llm_medium_temperature,
                "max_tokens": settings.llm_medium_max_tokens,
            }
        else:  # LIGHT
            return {
                "provider": settings.llm_light_provider,
                "model": settings.llm_light_model,
                "temperature": settings.llm_light_temperature,
                "max_tokens": settings.llm_light_max_tokens,
            }

    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_llm(cls, tier: LLMTier, fallback: bool = True):
        """
        Get LLM instance for specified tier.

        Args:
            tier: LLM tier (high/medium/light)
            fallback: Enable fallback to lower tier on failure

        Returns:
            LLM instance

        Raises:
            Exception: If all tiers fail
        """
        try:
            config = cls._get_config(tier)
            provider = config["provider"]

            logger.info(
                "creating_llm",
                tier=tier,
                provider=provider,
                model=config["model"]
            )

            if provider == "anthropic":
                return ChatAnthropic(
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    anthropic_api_key=settings.anthropic_api_key
                )
            elif provider == "openai":
                # Support custom OpenAI-format API
                kwargs = {
                    "model": config["model"],
                    "temperature": config["temperature"],
                    "max_tokens": config["max_tokens"],
                }

                if settings.openai_api_key:
                    kwargs["openai_api_key"] = settings.openai_api_key

                if settings.openai_api_base:
                    kwargs["openai_api_base"] = settings.openai_api_base

                return ChatOpenAI(**kwargs)
            elif provider == "ollama":
                from langchain_community.llms import Ollama
                return Ollama(
                    model=config["model"],
                    temperature=config["temperature"]
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")

        except Exception as e:
            logger.error(
                "llm_creation_failed",
                tier=tier,
                error=str(e)
            )

            # Fallback strategy: high -> medium -> light
            if fallback and tier != LLMTier.LIGHT:
                next_tier = LLMTier.MEDIUM if tier == LLMTier.HIGH else LLMTier.LIGHT
                logger.warning(
                    "falling_back_to_lower_tier",
                    from_tier=tier,
                    to_tier=next_tier
                )
                return cls.get_llm(next_tier, fallback=False)

            raise
