# app/config/settings.py
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables (.env).
    Uses pydantic-settings to validate values.
    """

    # Allow loading from .env and ignore extra variables
    # (extra variables may exist if .env is shared with other services)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- AWS / LocalStack configuration ---
    AWS_ACCESS_KEY_ID: str = Field(default="test")
    AWS_SECRET_ACCESS_KEY: str = Field(default="test")
    AWS_REGION: str = Field(default="us-east-1")

    # LocalStack endpoint (default is the standard port 4566)
    LOCALSTACK_ENDPOINT: AnyUrl = Field(default="http://localhost:4566")

    # Optional: some teams may prefer using SQS_ENDPOINT_URL instead of LOCALSTACK_ENDPOINT
    SQS_ENDPOINT_URL: AnyUrl | None = None

    # AWS Account ID (for building fallback queue URLs in LocalStack)
    ACCOUNT_ID: str = Field(default="000000000000")

    # Queue name for device messages
    QUEUE_NAME: str = Field(default="device-messages")

    # --- Simulation knobs ---
    # Number of devices that will be simulated
    NUM_DEVICES: int = Field(default=3, ge=1)

    # Frequency (seconds) for generating and sending messages
    SEND_INTERVAL_SEC: int = Field(default=2, ge=1, le=5)

    # Optional: Database URL (ignored in this service but may exist in .env for others)
    DATABASE_URL: str | None = None

    # Helper property: resolve the effective SQS endpoint
    @property
    def endpoint(self) -> str:
        return str(self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT)

# Instantiate settings
settings = Settings()
