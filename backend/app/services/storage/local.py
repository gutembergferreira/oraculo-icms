from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.storage.base import StoredObject, StorageBackend


class LocalStorageBackend(StorageBackend):
    name = "local"

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.local_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        *,
        org_id: int,
        file_name: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        target_dir = self.base_path / str(org_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        safe_name = file_name.replace("/", "_")
        disk_path = target_dir / f"{timestamp}_{safe_name}"
        disk_path.write_bytes(content)
        return StoredObject(
            path=str(disk_path),
            content_type=content_type,
            size=len(content),
        )

    def read(self, *, path: str) -> bytes:
        return Path(path).read_bytes()
