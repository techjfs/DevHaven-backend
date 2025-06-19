from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class RedisConfig(BaseSettings):
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis server host",
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis server port",
    )
    REDIS_DB: int = Field(
        default=0,
        description="Redis database number",
    )
    REDIS_PASSWORD: str | None = None

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"