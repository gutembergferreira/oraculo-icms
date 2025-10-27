from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.org_setting import OrgSetting
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.services.plan_catalog import PLAN_CATALOG
from app.services.app_settings import AppSettingsService

logger = logging.getLogger(__name__)


class StripeConfigurationError(Exception):
    pass


class StripeBillingService:
    """Integrações com Stripe para billing recorrente."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._app_settings = AppSettingsService(session)
        stored = self._app_settings.get_many(
            [
                "stripe_public_key",
                "stripe_secret_key",
                "stripe_webhook_secret",
            ]
        )
        self._public_key = stored.get("stripe_public_key") or settings.stripe_public_key
        self._secret_key = stored.get("stripe_secret_key") or settings.stripe_secret_key
        self._webhook_secret = (
            stored.get("stripe_webhook_secret") or settings.stripe_webhook_secret
        )
        if not self._secret_key:
            raise StripeConfigurationError(
                "Configuração Stripe ausente. Defina as credenciais da Stripe."
            )
        stripe.api_key = self._secret_key

    # ------------------------------------------------------------------
    def sync_plan_catalog(self) -> None:
        """Garante que produtos e preços existam no Stripe."""

        for plan_def in PLAN_CATALOG:
            plan = (
                self.session.query(Plan).filter(Plan.code == plan_def["code"]).one_or_none()
            )
            if not plan:
                continue

            try:
                product_id = self._ensure_product(plan, plan_def)
                price_id = self._ensure_price(plan, plan_def, product_id)
            except stripe.error.StripeError as exc:  # pragma: no cover - erro externo
                logger.warning("Não foi possível sincronizar plano %s: %s", plan.code, exc)
                continue

            plan.stripe_product_id = product_id
            plan.stripe_price_id = price_id
            self.session.add(plan)

    # ------------------------------------------------------------------
    def create_checkout_session(
        self,
        *,
        org: Organization,
        plan_code: str,
        customer_email: str,
    ) -> str:
        plan = self.session.query(Plan).filter(Plan.code == plan_code).one_or_none()
        if not plan:
            raise ValueError("Plano informado não existe")
        if plan.monthly_price_cents == 0:
            raise ValueError("Plano gratuito não requer checkout")
        if not plan.stripe_price_id:
            raise ValueError(
                "Plano sem preço Stripe configurado. Execute a sincronização de billing."
            )

        subscription = (
            self.session.query(Subscription)
            .filter(Subscription.org_id == org.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        success_url = self._frontend_url_with_state("success")
        cancel_url = self._frontend_url_with_state("cancelled")
        payload: dict[str, Any] = {
            "success_url": success_url,
            "cancel_url": cancel_url,
            "mode": "subscription",
            "line_items": [
                {"price": plan.stripe_price_id, "quantity": 1},
            ],
            "metadata": {"org_id": str(org.id), "plan_code": plan.code},
        }
        if subscription and subscription.stripe_customer_id:
            payload["customer"] = subscription.stripe_customer_id
        else:
            payload["customer_email"] = customer_email

        checkout = stripe.checkout.Session.create(**payload)
        if subscription is None:
            subscription = Subscription(org_id=org.id, plan=plan, status="pending")
        else:
            subscription.plan = plan
            subscription.status = "pending"
        self.session.add(subscription)
        return checkout["url"]

    # ------------------------------------------------------------------
    def create_portal_session(self, *, org: Organization) -> str:
        subscription = (
            self.session.query(Subscription)
            .filter(Subscription.org_id == org.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("Organização não possui assinatura Stripe ativa")

        portal = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=self._frontend_url(),
        )
        return portal["url"]

    # ------------------------------------------------------------------
    def parse_webhook(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        if not self._webhook_secret:
            raise StripeConfigurationError(
                "Webhook secret ausente. Defina STRIPE_WEBHOOK_SECRET."
            )
        return stripe.Webhook.construct_event(
            payload,
            signature,
            self._webhook_secret,
        )

    # ------------------------------------------------------------------
    def handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        logger.info("Stripe event recebido: %s", event_type)
        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(data)
        elif event_type == "invoice.payment_failed":
            self._handle_payment_failed(data)

    # ------------------------------------------------------------------
    def _handle_checkout_completed(self, session_payload: dict[str, Any]) -> None:
        metadata = session_payload.get("metadata") or {}
        org_id = int(metadata.get("org_id", 0))
        if not org_id:
            return
        subscription_id = session_payload.get("subscription")
        customer_id = session_payload.get("customer")
        if not subscription_id or not customer_id:
            return

        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        plan = self._resolve_plan_from_subscription(stripe_sub, metadata.get("plan_code"))
        if not plan:
            logger.warning("Plano não localizado para assinatura %s", subscription_id)
            return
        subscription = self._upsert_subscription(org_id, plan, stripe_sub)
        subscription.stripe_customer_id = customer_id
        self.session.add(subscription)
        self._apply_plan_to_org(org_id, plan, stripe_sub)

    # ------------------------------------------------------------------
    def _handle_subscription_updated(self, subscription_payload: dict[str, Any]) -> None:
        plan = self._resolve_plan_from_subscription(subscription_payload)
        org_id = self._extract_org_id(subscription_payload)
        if not org_id:
            return
        if plan:
            subscription = self._upsert_subscription(org_id, plan, subscription_payload)
            self.session.add(subscription)
            if subscription_payload.get("status") in {"active", "trialing", "past_due"}:
                self._apply_plan_to_org(org_id, plan, subscription_payload)
            else:
                free_plan = self._get_plan("FREE")
                if free_plan:
                    self._apply_plan_to_org(org_id, free_plan, subscription_payload, reset_usage=False)
        else:
            logger.warning(
                "Plano não identificado na atualização de assinatura %s",
                subscription_payload.get("id"),
            )

    # ------------------------------------------------------------------
    def _handle_subscription_deleted(self, subscription_payload: dict[str, Any]) -> None:
        org_id = self._extract_org_id(subscription_payload)
        if not org_id:
            return
        free_plan = self._get_plan("FREE")
        if free_plan:
            subscription = self._upsert_subscription(org_id, free_plan, subscription_payload)
            subscription.status = "canceled"
            self.session.add(subscription)
            self._apply_plan_to_org(org_id, free_plan, subscription_payload, reset_usage=False)

    # ------------------------------------------------------------------
    def _handle_payment_failed(self, invoice_payload: dict[str, Any]) -> None:
        subscription_id = invoice_payload.get("subscription")
        if not subscription_id:
            return
        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        org_id = self._extract_org_id(stripe_sub)
        if not org_id:
            return
        subscription = self._upsert_subscription(
            org_id,
            self._resolve_plan_from_subscription(stripe_sub) or self._get_plan("FREE"),
            stripe_sub,
        )
        subscription.status = "past_due"
        self.session.add(subscription)
        free_plan = self._get_plan("FREE")
        if free_plan:
            self._apply_plan_to_org(org_id, free_plan, stripe_sub, reset_usage=False)
            setting = self.session.query(OrgSetting).filter(OrgSetting.org_id == org_id).one_or_none()
            if setting:
                flags = dict(setting.flags or {})
                flags["billing_status"] = "payment_failed"
                setting.flags = flags
                self.session.add(setting)

    # ------------------------------------------------------------------
    def _ensure_product(self, plan: Plan, plan_def: dict[str, Any]) -> str:
        if plan.stripe_product_id:
            try:
                stripe.Product.modify(
                    plan.stripe_product_id,
                    name=plan_def["name"],
                    metadata={"plan_code": plan.code},
                )
                return plan.stripe_product_id
            except stripe.error.InvalidRequestError:
                logger.info("Produto %s inexistente, será recriado", plan.stripe_product_id)
        product = stripe.Product.create(
            name=plan_def["name"],
            metadata={
                "plan_code": plan.code,
                "handle": plan_def.get("stripe_product_handle") or plan.code.lower(),
            },
        )
        return product["id"]

    def _ensure_price(
        self, plan: Plan, plan_def: dict[str, Any], product_id: str
    ) -> str | None:
        if plan_def.get("monthly_price_cents") in (None, 0):
            return None

        lookup_key = plan_def.get("stripe_price_lookup_key") or f"{plan.code.lower()}_monthly"
        if plan.stripe_price_id:
            try:
                price = stripe.Price.retrieve(plan.stripe_price_id)
                if price["unit_amount"] == plan_def["monthly_price_cents"]:
                    return price["id"]
            except stripe.error.InvalidRequestError:
                logger.info("Preço %s inexistente, criando novo", plan.stripe_price_id)

        price_list = stripe.Price.list(product=product_id, active=True, limit=20)
        for price in price_list.data:
            if price.get("lookup_key") == lookup_key and price["unit_amount"] == plan_def["monthly_price_cents"]:
                return price["id"]

        price = stripe.Price.create(
            product=product_id,
            unit_amount=plan_def["monthly_price_cents"],
            currency="brl",
            recurring={"interval": "month"},
            lookup_key=lookup_key,
        )
        return price["id"]

    # ------------------------------------------------------------------
    def _upsert_subscription(
        self,
        org_id: int,
        plan: Plan,
        stripe_payload: dict[str, Any],
    ) -> Subscription:
        subscription = (
            self.session.query(Subscription)
            .filter(Subscription.org_id == org_id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        if not subscription:
            subscription = Subscription(org_id=org_id, plan=plan)
            self.session.add(subscription)
        subscription.plan = plan
        subscription.status = stripe_payload.get("status", subscription.status)
        subscription.stripe_subscription_id = stripe_payload.get("id")
        subscription.current_period_start = self._ts_to_datetime(
            stripe_payload.get("current_period_start")
        )
        subscription.current_period_end = self._ts_to_datetime(
            stripe_payload.get("current_period_end")
        )
        subscription.cancel_at = self._ts_to_datetime(stripe_payload.get("cancel_at"))
        return subscription

    def _apply_plan_to_org(
        self,
        org_id: int,
        plan: Plan,
        stripe_payload: dict[str, Any] | None,
        *,
        reset_usage: bool = True,
    ) -> None:
        setting = self.session.query(OrgSetting).filter(OrgSetting.org_id == org_id).one_or_none()
        if not setting:
            setting = OrgSetting(org_id=org_id)
        setting.current_plan_id = plan.id
        setting.plan_limits = plan.limits or {}
        setting.plan_features = plan.features or {}
        flags = dict(setting.flags or {})
        flags.update({key: bool(value) for key, value in setting.plan_features.items() if isinstance(value, bool)})
        flags["plan_code"] = plan.code
        setting.flags = flags
        if reset_usage:
            setting.xml_uploaded_count_month = 0
        if stripe_payload:
            setting.usage_period_start = self._ts_to_datetime(
                stripe_payload.get("current_period_start")
            )
            setting.usage_period_end = self._ts_to_datetime(
                stripe_payload.get("current_period_end")
            )
        self.session.add(setting)

    def _resolve_plan_from_subscription(
        self, stripe_payload: dict[str, Any], plan_code_hint: str | None = None
    ) -> Plan | None:
        price_id = None
        items = stripe_payload.get("items", {}).get("data") or []
        if items:
            price = (items[0] or {}).get("price") or {}
            price_id = price.get("id") or price.get("price")
        if price_id:
            plan = (
                self.session.query(Plan)
                .filter(Plan.stripe_price_id == price_id)
                .one_or_none()
            )
            if plan:
                return plan
        if plan_code_hint:
            return self._get_plan(plan_code_hint)
        return None

    def _extract_org_id(self, stripe_payload: dict[str, Any]) -> int | None:
        metadata = stripe_payload.get("metadata") or {}
        if "org_id" in metadata:
            try:
                return int(metadata["org_id"])
            except (TypeError, ValueError):
                return None
        customer_id = stripe_payload.get("customer")
        if customer_id:
            subscription = (
                self.session.query(Subscription)
                .filter(Subscription.stripe_customer_id == customer_id)
                .first()
            )
            if subscription:
                return subscription.org_id
        return None

    def _get_plan(self, code: str) -> Plan | None:
        return self.session.query(Plan).filter(Plan.code == code).one_or_none()

    @staticmethod
    def _frontend_url() -> str:
        return str(settings.frontend_url or "http://localhost:5173/billing")

    @classmethod
    def _frontend_url_with_state(cls, state: str) -> str:
        base = cls._frontend_url()
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}state={state}"

    @staticmethod
    def _ts_to_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return None
