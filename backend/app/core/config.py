from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GENERATOR_MODEL: str = ""
    DB_PATH: str = "data/research.db"
    CHROMA_PATH: str = "data/chroma"
    MAX_SOURCES_PER_SUBQUESTION: int = 3
    MAX_SUBQUESTIONS: int = 5
    CONFIDENCE_THRESHOLD: float = 0.3
    SCRAPER_TIMEOUT: int = 15
    MAX_RETRIES: int = 2
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __repr__(self) -> str:
        return f"<Settings provider={self.PROVIDER}>"


settings = Settings()
