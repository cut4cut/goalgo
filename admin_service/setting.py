from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000

    connection_string: str = "postgresql+asyncpg://user:pass@localhost:5432/postgres"

    allow_origins: list[str] = []

    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
