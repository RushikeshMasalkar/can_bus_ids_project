"""Configuration for backend runtime paths and environment overrides."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Environment-backed settings for backend model asset paths."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_ROOT: Path = PROJECT_ROOT
    MODEL_PATH: Path = Field(default=PROJECT_ROOT / "models" / "best_model.pt")
    VOCAB_PATH: Path = Field(default=PROJECT_ROOT / "data" / "vocab.json")
    THRESHOLD_PATH: Path = Field(default=PROJECT_ROOT / "models" / "threshold.json")
    MULTICLASS_MODEL_PATH: Path = Field(default=PROJECT_ROOT / "models" / "multiclass_model.pkl")
    MULTICLASS_VECTORIZER_PATH: Path = Field(default=PROJECT_ROOT / "models" / "vectorizer.pkl")

    @field_validator(
        "MODEL_PATH",
        "VOCAB_PATH",
        "THRESHOLD_PATH",
        "MULTICLASS_MODEL_PATH",
        "MULTICLASS_VECTORIZER_PATH",
        mode="before",
    )
    @classmethod
    def resolve_project_relative_path(cls, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()


settings = Settings()
