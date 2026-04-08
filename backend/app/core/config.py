from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Agent Chat"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_chat"

    # Redis (agent memory / pub-sub)
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Providers
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Search API (Tavily, SerpAPI, etc.)
    SEARCH_API_KEY: str = ""
    SEARCH_PROVIDER: str = "tavily"

    # Agent defaults
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    MAX_AGENT_STEPS: int = 25
    AGENT_TIMEOUT_SECONDS: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
