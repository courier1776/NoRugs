from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "norugs"
    db_user: str = "brendanwebb"
    db_password: str = ""

    coingecko_api_key: str = ""
    coingecko_plan: str = "demo"
    etherscan_api_key: str = ""
    github_token: str = ""

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
