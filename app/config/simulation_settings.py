from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl, BaseModel

from app.config.aws_settings import AwsSettings
from app.config.db_settings import DbSettings


class SimulationSettings(BaseSettings):
    """Simulation knobs."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="SIM_")
    NUM_DEVICES: int = Field(default=3, ge=1)
    SEND_INTERVAL_SEC: int = Field(default=2, ge=1, le=5)


aws = AwsSettings()
db = DbSettings()
sim = SimulationSettings()