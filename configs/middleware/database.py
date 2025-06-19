from pydantic import Field, computed_field
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseSettings):
    DB_TYPE: str = Field(
        default="postgresql",
        description="Database type (e.g., postgresql, mysql, sqlite)",
    )
    DB_HOST: str = Field(
        default="localhost",
        description="Database host address",
    )
    DB_PORT: int = Field(
        default=5432,
        description="Database port number",
    )
    DB_DATABASE: str = Field(
        default="devhaven",
        description="Database name",
    )
    DB_USERNAME: str = Field(
        default="postgres",
        description="Database username",
    )
    DB_PASSWORD: str = Field(
        default="postgres",
        description="Database password",
    )

    DB_CHARSET: str = Field(
        default="utf8",
    )

    DB_EXTRAS: str = Field(
        default="",
        description="Additional parameters for the database connection",
    )

    SQLALCHEMY_DATABSE_URI_SCHEME: str = Field(
        default="postgresql+psycopg2",
        description="Database URI scheme for SQLAlchemy",
    )

    SQLALCHEMY_POOL_PRE_PING: bool = Field(
        default=True,
        description="Enable pool pre-ping to check connection validity",
    )

    SQLALCHEMY_POOL_RECYCLE: int = Field(
        default=1800,
        description="Connection pool recycle time in seconds",
    )
    SQLALCHEMY_POOL_SIZE: int = Field(
        default=10,
        description="Connection pool size",
    )
    SQLALCHEMY_MAX_OVERFLOW: int = Field(
        default=20,
        description="Maximum number of connections to create beyond the pool size",
    )

    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        extra_params = (
            f"{self.DB_EXTRAS}&client_encoding={self.DB_CHARSET}" if self.DB_CHARSET else self.DB_EXTRAS
        ).strip("&")
        extra_params = f"?{extra_params}" if extra_params else ""
        return (
            f"{self.SQLALCHEMY_DATABSE_URI_SCHEME}://"
            f"{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            f"{extra_params}"
        )
    
    @computed_field
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict:
        return {
            "pool_pre_ping": self.SQLALCHEMY_POOL_PRE_PING,
            "pool_recycle": self.SQLALCHEMY_POOL_RECYCLE,
            "pool_size": self.SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.SQLALCHEMY_MAX_OVERFLOW,
        }