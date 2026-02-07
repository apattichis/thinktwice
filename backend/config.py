"""Application configuration via environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # Required - Anthropic API
    anthropic_api_key: str

    # Optional - Search APIs (Brave -> Tavily -> None fallback)
    brave_search_api_key: str | None = None
    tavily_api_key: str | None = None

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # LLM Configuration
    model_name: str = "claude-3-5-haiku-20241022"
    max_tokens: int = 4096
    timeout: float = 60.0

    # Pipeline Configuration
    gate_threshold: int = 85
    gate_min_pass_rate: float = 1.0
    max_iterations: int = 3
    convergence_threshold: int = 80
    self_verify_enabled: bool = True
    self_verify_parallel: bool = True
    trust_blend_enabled: bool = True

    @property
    def has_search(self) -> bool:
        """Check if any search API is configured."""
        return bool(self.brave_search_api_key or self.tavily_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
