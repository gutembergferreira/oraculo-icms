from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.org_setting import OrgSetting


@dataclass(slots=True)
class PlanLimitError(Exception):
    """Erro de negócio quando a organização ultrapassa um limite de plano."""

    code: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - compat com Exception
        return self.message


class OrgPlanLimiter:
    """Aplica verificações e registra consumo de cotas."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_upload_quota(
        self, org_id: int, *, new_files: int = 0, new_bytes: int = 0
    ) -> OrgSetting:
        """Garante que há cota disponível para um novo upload."""

        setting = self._get_settings(org_id, for_update=True)
        limits = setting.plan_limits or {}
        if new_files:
            max_uploads = limits.get("max_xml_uploads_month")
            if isinstance(max_uploads, int) and max_uploads >= 0:
                if setting.xml_uploaded_count_month + new_files > max_uploads:
                    raise PlanLimitError(
                        "xml_uploads_limit", "Limite mensal de uploads excedido"
                    )
        if new_bytes:
            max_storage = limits.get("max_storage_mb")
            if isinstance(max_storage, int) and max_storage >= 0:
                projected = setting.storage_used_mb + self._bytes_to_mb(new_bytes)
                if projected > max_storage:
                    raise PlanLimitError(
                        "storage_limit", "Limite de armazenamento excedido"
                    )
        return setting

    def register_usage(
        self,
        setting: OrgSetting,
        *,
        uploaded_files: int = 0,
        added_bytes: int = 0,
    ) -> None:
        if uploaded_files:
            setting.xml_uploaded_count_month += uploaded_files
        if added_bytes:
            setting.storage_used_mb += self._bytes_to_mb(added_bytes)
        self.session.add(setting)

    def _get_settings(self, org_id: int, *, for_update: bool = False) -> OrgSetting:
        query = self.session.query(OrgSetting).filter(OrgSetting.org_id == org_id)
        if for_update:
            query = query.with_for_update()
        setting = query.one_or_none()
        if not setting:
            raise PlanLimitError(
                "org_settings_missing", "Configurações da organização não encontradas"
            )
        return setting

    @staticmethod
    def _bytes_to_mb(total_bytes: int) -> int:
        return max(1, math.ceil(total_bytes / (1024 * 1024))) if total_bytes else 0
