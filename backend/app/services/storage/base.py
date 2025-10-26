from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class StoredObject:
    """Representa um artefato armazenado em um backend de arquivos."""

    path: str
    content_type: str | None = None
    size: int | None = None


class StorageBackend(Protocol):
    """Interface simples para serviços de storage."""

    name: str

    def store(
        self,
        *,
        org_id: int,
        file_name: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        ...

    def read(self, *, path: str) -> bytes:
        ...
