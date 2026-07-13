"""Configuration module for PAN-OS firewall agent using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for PAN-OS firewall agent with environment variable support."""

    # PAN-OS Configuration
    PANOS_HOST: str
    PANOS_API_KEY: Optional[str] = None
    PANOS_USERNAME: Optional[str] = None
    PANOS_PASSWORD: Optional[SecretStr] = None
    PANOS_VSYS: str = "vsys1"
    PANOS_VERIFY_TLS: bool = True
    PANOS_TIMEOUT: int = 30
    PANOS_RATE_LIMIT: float = 10.0

    # Backup Configuration
    BACKUP_DIR: str = "./backups"

    # S3 Configuration
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_PREFIX: str = ""
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[SecretStr] = None
    S3_REGION: Optional[str] = None
    S3_USE_SSL: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @model_validator(mode="after")
    def validate_auth(self) -> "Settings":
        """
        Validate that either API key or username/password is provided.

        Raises:
            ValueError: If neither PANOS_API_KEY nor both PANOS_USERNAME
                       and PANOS_PASSWORD are set.
        """
        if not self.PANOS_API_KEY and not (
            self.PANOS_USERNAME and self.PANOS_PASSWORD
        ):
            raise ValueError(
                "Either PANOS_API_KEY or both PANOS_USERNAME and PANOS_PASSWORD must be set"
            )
        return self

    @property
    def base_url(self) -> str:
        """
        Return the base URL for PAN-OS API requests.

        Returns:
            str: The base API URL with trailing /api/ path.
        """
        return self.PANOS_HOST.rstrip("/") + "/api/"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Cached Settings instance loaded from environment variables.
    """
    return Settings()
