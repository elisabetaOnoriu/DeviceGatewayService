# app/config/settings.py
from __future__ import annotations
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.aws_settings import AwsSettings
from app.config.db_settings import DbSettings
from app.config.simulation_settings import SimulationSettings


class Settings(BaseSettings):
    """
    Application-wide settings composed from nested sections (AWS, DB, SIM).
    Loads values from environment variables (and .env) using nested keys with the
    delimiter "__" (e.g., AWS__REGION, DB__USER, SIM__NUM_DEVICES).
    Also supports a flat DATABASE_URL override for legacy compatibility.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )

    AWS: AwsSettings = AwsSettings()
    DB: DbSettings = DbSettings()
    SIM: SimulationSettings = SimulationSettings()

    DATABASE_URL: str | None = Field(default=None)

    def __init__(self, **values: Dict[str, Any]) -> None:
        """
        If a flat DATABASE_URL is supplied in the environment or .env, propagate it
        into the nested DB settings as `url_direct` to keep backward compatibility.
        """
        db_values = values.get("DB") or {}
        if values.get("DATABASE_URL") and not db_values.get("url_direct"):
            db_values = dict(db_values, url_direct=values["DATABASE_URL"])
            values["DB"] = db_values
        super().__init__(**values)


# Singleton to import across the app
settings = Settings()
