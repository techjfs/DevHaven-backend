from pydantic import Field
from pydantic_settings import BaseSettings


class GithubConfig(BaseSettings):
    GITHUB_CLIENT_ID: str = Field(
        default="",
        description="GitHub OAuth client ID",
    )
    GITHUB_CLIENT_SECRET: str = Field(  
        default="",
        description="GitHub OAuth client secret",
    )
    GITHUB_REDIRECT_URI: str = Field(
        default="",
        description="GitHub OAuth redirect URI",
    )
    GITHUB_SCOPE: str = Field(
        default="",
        description="GitHub OAuth scope",
    ) # e.g., "user:email"
    GITHUB_AUTH_URL: str = Field(
        default="",
        description="GitHub OAuth authorization URL",
    )