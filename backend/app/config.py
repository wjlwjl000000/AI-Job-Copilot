from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://copilot:copilot123@localhost:5432/copilot"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # openai_api_key: str = "sk-AfFjOyI0IT8ZELF7mXMQ3voviAIwDYaGvoJnxfpGOcJpXWAj"
    openai_api_key: str = "sk-qii5tHmGIASrA2oJYsJTxZL9Ona7tu3PfLW6ho16oiMWdFMm"
    openai_base_url: str = "https://api.chatanywhere.tech"
    openai_model: str = "gpt-5-mini"

    class Config:
        env_file = ".env"

settings = Settings()
