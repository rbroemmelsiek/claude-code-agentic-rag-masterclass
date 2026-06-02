from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # OpenAI
    openai_api_key: str
    openai_vector_store_id: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-masterclass"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars like old OPENAI_ASSISTANT_ID


@lru_cache
def get_settings() -> Settings:
    return Settings()
