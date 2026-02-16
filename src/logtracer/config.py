"""Runtime configuration for logtracer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .storage.base import StorageBackend
from .storage.file import FileStore
from .storage.memory import MemoryStore

CaptureLevel = Literal["minimal", "standard", "full"]


@dataclass(slots=True)
class Settings:
    capture_level: CaptureLevel = "full"
    auto_instrument: list[str] = field(default_factory=list)
    storage: StorageBackend = field(default_factory=MemoryStore)
    redact_patterns: list[str] = field(default_factory=list)
    max_output_size: int | None = None


_settings = Settings()


def configure(
    capture_level: CaptureLevel = "full",
    auto_instrument: list[str] | None = None,
    storage: str | StorageBackend = "memory",
    redact_patterns: list[str] | None = None,
    max_output_size: int | None = None,
) -> None:
    """Update global runtime configuration."""
    _settings.capture_level = capture_level
    _settings.auto_instrument = list(auto_instrument or [])
    _settings.storage = _resolve_storage(storage)
    _settings.redact_patterns = list(redact_patterns or [])
    _settings.max_output_size = max_output_size


def get_settings() -> Settings:
    """Return current global settings."""
    return _settings


def _resolve_storage(storage: str | StorageBackend) -> StorageBackend:
    """Resolve storage from shorthand string or backend instance."""
    if not isinstance(storage, str):
        return storage
    if storage == "memory":
        return MemoryStore()
    if storage.startswith("file://"):
        return FileStore(storage.removeprefix("file://"))
    raise ValueError(
        "Unsupported storage value. Use 'memory', 'file://<path>', or a StorageBackend instance."
    )
