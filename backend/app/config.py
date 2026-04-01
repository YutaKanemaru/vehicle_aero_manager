from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Application
    app_name: str = "VAM"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./vam.db"

    # JWT
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Storage
    upload_dir: Path = Path("./uploads")
    result_dir: Path = Path("./results")

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]  # Vite dev server

    model_config = {"env_file": ".env", "env_prefix": "VAM_"}


settings = Settings()
