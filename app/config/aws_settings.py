from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl

class AwsSettings(BaseSettings):
    """AWS / LocalStack settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="AWS_")
    ACCESS_KEY_ID: str = "test"
    SECRET_ACCESS_KEY: str = "test"
    REGION: str = "us-east-1"
    LOCALSTACK_ENDPOINT: AnyUrl = "http://localhost:4566"
    SQS_ENDPOINT_URL: AnyUrl | None = None
    ACCOUNT_ID: str = "000000000000"
    QUEUE_NAME: str = "device-messages"

    @property
    def endpoint(self) -> str:
        return str(self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT)