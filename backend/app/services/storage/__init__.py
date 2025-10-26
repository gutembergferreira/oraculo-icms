from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorageBackend

try:
    from app.services.storage.s3 import S3StorageBackend
except Exception:  # pragma: no cover - falha opcional de import
    S3StorageBackend = None  # type: ignore


@lru_cache()
def _get_local_backend() -> StorageBackend:
    return LocalStorageBackend()


@lru_cache()
def _get_s3_backend() -> StorageBackend:
    if S3StorageBackend is None:
        raise RuntimeError("Backend S3/MinIO indisponível: dependências não carregadas")
    return S3StorageBackend()


def get_storage_backend(name: str | None = None) -> StorageBackend:
    backend = (name or settings.storage_backend).lower()
    if backend in {"s3", "minio"}:
        return _get_s3_backend()
    return _get_local_backend()
