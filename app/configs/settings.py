from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str
    APP_ENV: str = "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()