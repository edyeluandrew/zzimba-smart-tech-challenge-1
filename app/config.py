from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    # Local default. Production is a Neon Postgres URL (see .env.example).
    database_url: str = "sqlite:///./luweero.db"
    # Neon direct host, used by Alembic. Blank falls back to database_url.
    direct_database_url: str = ""
    cloud_storage_public_base_url: str = (
        "https://luweero-blueprints.fra1.digitaloceanspaces.com"
    )
    cloud_storage_bucket: str = "luweero-blueprints"
    cloud_storage_access_key_id: str = ""
    cloud_storage_secret_access_key: str = ""


settings = Settings()
