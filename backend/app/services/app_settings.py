from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting


class AppSettingsService:
    """Permite leitura e escrita de configurações globais persistidas."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str) -> str | None:
        setting = self.session.get(AppSetting, key)
        return setting.value if setting else None

    def get_many(self, keys: Iterable[str]) -> dict[str, str | None]:
        records = (
            self.session.query(AppSetting)
            .filter(AppSetting.key.in_(list(keys)))
            .all()
        )
        return {record.key: record.value for record in records}

    def set(self, key: str, value: str | None, *, user_id: int | None = None) -> AppSetting:
        setting = self.session.get(AppSetting, key)
        if setting is None:
            setting = AppSetting(key=key)
        setting.value = value
        setting.updated_by_id = user_id
        setting.updated_at = datetime.utcnow()
        self.session.add(setting)
        return setting

    def delete(self, key: str) -> None:
        setting = self.session.get(AppSetting, key)
        if setting is not None:
            self.session.delete(setting)
