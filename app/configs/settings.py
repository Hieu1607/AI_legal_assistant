from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str
    APP_HOST: str
    APP_PORT: int
    WEAVIATE_COLLECTION_NAME: str
    SYSTEM_PROMPT_PATH: str = "app/configs/system_prompt.txt"
    GROQ_API_KEY: str
    GROQ_SYSTEM_PROMPT_PATH: str = "app/configs/groq_system_prompt.txt"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
