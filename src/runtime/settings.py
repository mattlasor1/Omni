from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OmniSettings:
    project_root: Path
    data_dir: Path
    model_dir: Path
    log_dir: Path
    vector_store_path: Path
    cache_store_path: Path
    training_store_path: Path
    offline_strict: bool
    enable_model_downloads: bool
    enable_swarm: bool
    allow_lan: bool
    enable_external_devices: bool
    enable_local_maintenance: bool
    maintenance_ingest_interval_seconds: int
    maintenance_reflection_interval_seconds: int
    maintenance_growth_interval_seconds: int
    maintenance_review_interval_seconds: int
    api_host: str
    api_port: int
    frontend_host: str
    frontend_port: int

    @property
    def cors_origins(self) -> list[str]:
        return [
            f"http://{self.frontend_host}:{self.frontend_port}",
            f"http://127.0.0.1:{self.frontend_port}",
            f"http://localhost:{self.frontend_port}",
        ]

    @property
    def frontend_url(self) -> str:
        return f"http://{self.frontend_host}:{self.frontend_port}"

    @property
    def backend_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> OmniSettings:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = Path(os.getenv("OMNI_DATA_DIR", str(project_root / "data"))).resolve()
    model_dir = Path(os.getenv("OMNI_MODEL_DIR", str(project_root / "models"))).resolve()

    settings = OmniSettings(
        project_root=project_root,
        data_dir=data_dir,
        model_dir=model_dir,
        log_dir=data_dir / "logs",
        vector_store_path=data_dir / "vector_store.json",
        cache_store_path=data_dir / "cache_store.json",
        training_store_path=data_dir / "training_state.json",
        offline_strict=_as_bool(os.getenv("OMNI_OFFLINE_STRICT"), True),
        enable_model_downloads=_as_bool(os.getenv("OMNI_ENABLE_MODEL_DOWNLOADS"), False),
        enable_swarm=_as_bool(os.getenv("OMNI_ENABLE_SWARM"), False),
        allow_lan=_as_bool(os.getenv("OMNI_ALLOW_LAN"), False),
        enable_external_devices=_as_bool(os.getenv("OMNI_ENABLE_EXTERNAL_DEVICES"), False),
        enable_local_maintenance=_as_bool(os.getenv("OMNI_ENABLE_LOCAL_MAINTENANCE"), True),
        maintenance_ingest_interval_seconds=int(os.getenv("OMNI_MAINTENANCE_INGEST_INTERVAL_SECONDS", "15")),
        maintenance_reflection_interval_seconds=int(os.getenv("OMNI_MAINTENANCE_REFLECTION_INTERVAL_SECONDS", "90")),
        maintenance_growth_interval_seconds=int(os.getenv("OMNI_MAINTENANCE_GROWTH_INTERVAL_SECONDS", "180")),
        maintenance_review_interval_seconds=int(os.getenv("OMNI_MAINTENANCE_REVIEW_INTERVAL_SECONDS", "120")),
        api_host=os.getenv("OMNI_API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("OMNI_API_PORT", "8000")),
        frontend_host=os.getenv("OMNI_FRONTEND_HOST", "127.0.0.1"),
        frontend_port=int(os.getenv("OMNI_FRONTEND_PORT", "3000")),
    )
    settings.ensure_directories()
    return settings
