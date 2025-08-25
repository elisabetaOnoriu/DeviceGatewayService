from pydantic_settings import BaseSettings, SettingsConfigDict

class DbSettings(BaseSettings):
    """Database connection pieces."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="DB_")
    USER: str = "tds_user"
    PASSWORD: str = "Parola123!"
    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "tds_db"
    """ no prefix: pick up DATABASE_URL directly if present"""
    DATABASE_URL: str | None = None

    @property
    def url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"