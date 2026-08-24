"""Configuración central vía variables de entorno (.env)."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Base de datos ──────────────────────────────────────────────
    database_url: str

    # ── Almacenamiento local ───────────────────────────────────────
    store_path: Path = Path("/store")

    @property
    def originals_dir(self) -> Path:
        return self.store_path / "originals"

    @property
    def outputs_dir(self) -> Path:
        return self.store_path / "outputs"

    @property
    def previews_dir(self) -> Path:
        return self.store_path / "previews"

    @property
    def audit_log_path(self) -> Path:
        return self.store_path / "audit.jsonl"

    # ── Seguridad ──────────────────────────────────────────────────
    secret_key: str

    # ── Límites ────────────────────────────────────────────────────
    max_file_size_mb: int = 100
    default_expiry_days: int = 30

    # ── CORS ───────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    def ensure_dirs(self) -> None:
        """Crea carpetas del store si no existen."""
        for d in (self.originals_dir, self.outputs_dir, self.previews_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
