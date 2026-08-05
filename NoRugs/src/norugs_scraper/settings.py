from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "norugs"
    db_user: str = "postgres"
    db_password: str = ""

    coingecko_api_key: str = ""
    coingecko_plan: str = "demo"
    etherscan_api_key: str = ""
    github_token: str = ""

    # Caps how many assets (coingecko_ids, dex_tokens, etherscan_tokens,
    # github_repositories) are collected per config file, so the app stays
    # within free/unauthenticated provider rate limits without needing any
    # API keys. 50 is a safe default for GitHub's unauthenticated 60
    # requests/hour cap once combined with the throttling below.
    max_tracked_assets: int = Field(default=50, ge=1)

    # GitHub's unauthenticated API allows only 60 requests/hour, and this
    # app makes 4 requests per repository (repo info, commits, contributors,
    # closed issues). Without a token, refreshing more than ~10 repos an
    # hour risks a 403. These two settings keep GitHub collection safe by
    # only refreshing a rotating batch of repos at a conservative interval,
    # regardless of how many repositories are configured.
    github_refresh_interval_seconds: int = Field(default=3600, ge=60)
    github_max_repos_per_run: int = Field(default=10, ge=1)

    http_timeout_seconds: float = Field(default=30, gt=0)
    log_level: str = "INFO"

    live_updates_enabled: bool = True
    live_update_interval_seconds: int = Field(default=60, ge=15)
    live_update_on_start: bool = True

    @property
    def database_url(self) -> str:
        password = f":{self.db_password}" if self.db_password else ""
        return (
            f"postgresql://{self.db_user}{password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )
