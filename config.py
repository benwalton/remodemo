from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_USER: str = "benuser"
    MONGO_PASSWORD: str = "password007"
    MONGO_CONNECTION_STRING: str = "mongodb://localhost"
    MONGO_DATABASE: str = "remodemo"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
