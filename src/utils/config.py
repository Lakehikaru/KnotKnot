"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # LLM Configuration
    llm_high_provider: str = "anthropic"
    llm_high_model: str = "claude-opus-4-6"
    llm_high_temperature: float = 0.1
    llm_high_max_tokens: int = 4096

    llm_medium_provider: str = "anthropic"
    llm_medium_model: str = "claude-sonnet-4-6"
    llm_medium_temperature: float = 0.3
    llm_medium_max_tokens: int = 4096

    llm_light_provider: str = "ollama"
    llm_light_model: str = "qwen3.5:32b"
    llm_light_temperature: float = 0.5
    llm_light_max_tokens: int = 2048

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Storage
    chroma_path: str = "./data/chroma_db"
    chroma_collection_name: str = "documents"

    # Performance
    batch_size: int = 20
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 10
    max_retrieval_iterations: int = 5
    max_workers: int = 4

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    log_max_size: int = 10485760
    log_backup_count: int = 5

    # Cache
    enable_cache: bool = True
    cache_ttl: int = 3600
    semantic_cache_threshold: float = 0.95

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
