from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl, BaseModel


class AwsSettings(BaseSettings):
    """AWS / LocalStack settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ACCESS_KEY_ID: str = "test"
    SECRET_ACCESS_KEY: str = "test"
    AWS_REGION: str = "us-east-1"
    LOCALSTACK_ENDPOINT: AnyUrl = "http://localhost:4566"
    SQS_ENDPOINT_URL: AnyUrl | None = None
    ACCOUNT_ID: str = "000000000000"
    QUEUE_NAME: str = "terminal-messages"

    @property
    def endpoint(self) -> str:
        return str(self.SQS_ENDPOINT_URL or self.LOCALSTACK_ENDPOINT)