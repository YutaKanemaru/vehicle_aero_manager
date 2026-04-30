from pydantic_settings import BaseSettings
from pathlib import Path

# backend/ ディレクトリの絶対パス（どこから起動しても同じDBを参照）
_BACKEND_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    # Application
    app_name: str = "VAM"
    debug: bool = True

    # Database — 絶対パスをデフォルト値にする
    database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'vam.db'}"

    # JWT
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Storage — 絶対パスで固定（起動ディレクトリ依存を防ぐ）
    upload_dir: Path = _BACKEND_DIR / "data" / "uploads"
    result_dir: Path = _BACKEND_DIR / "data" / "results"
    runs_dir: Path = _BACKEND_DIR / "data" / "runs"
    viewer_cache_dir: Path = _BACKEND_DIR / "data" / "viewer_cache"
    transformed_dir: Path = _BACKEND_DIR / "data" / "transformed"  # ride-height/yaw transform output STLs

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]  # Vite dev server

    model_config = {"env_file": ".env", "env_prefix": "VAM_"}


settings = Settings()
