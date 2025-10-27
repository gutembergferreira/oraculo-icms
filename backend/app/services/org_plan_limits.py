from __future__ import annotations

import math
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.org_setting import OrgSetting
from app.models.organization import Organization


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
        if setting:
            return setting

        org = self.session.get(Organization, org_id)
        if not org:
            raise PlanLimitError(
                "org_not_found", "Organização não encontrada para verificação de limites"
            )

        plan = None
        if org.subscriptions:
            for subscription in sorted(
                org.subscriptions,
                key=lambda sub: sub.created_at or datetime.min,
                reverse=True,
            ):
                if getattr(subscription, "plan", None):
                    plan = subscription.plan
                    break

        setting = OrgSetting(org_id=org_id)
        if plan:
            setting.current_plan_id = plan.id
            setting.plan_limits = plan.limits or {}
            setting.plan_features = plan.features or {}
            setting.flags = {
                **{key: bool(value) for key, value in (plan.features or {}).items()},
                "plan_code": plan.code,
            }
        self.session.add(setting)
        self.session.flush()
        return setting

    @staticmethod
    def _bytes_to_mb(total_bytes: int) -> int:
        return max(1, math.ceil(total_bytes / (1024 * 1024))) if total_bytes else 0
