from pydantic_settings import SettingsConfigDict
from pydantic import Field

from .auth import AuthConfig
from .middleware.redis import RedisConfig
from .middleware.database import DatabaseConfig


class AppConfig(
    AuthConfig,
    RedisConfig,
    DatabaseConfig,
    ):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra="ignore")

    # Application settings
    APP_NAME: str = Field(
        default="DevHaven",
        description="Name of the application",
    )
    APP_VERSION: str = Field(
        default="0.1.0",
        description="Version of the application",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode",
    )