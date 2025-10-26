import stripe

from app.core.config import settings
from app.models.org_setting import OrgSetting
from app.models.subscription import Subscription


def test_create_checkout_session_success(client, session, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test", raising=False)
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test", raising=False)

    def fake_checkout_create(**kwargs):
        assert kwargs["metadata"]["plan_code"] == "PRO"
        return {"url": "https://stripe.test/checkout/pro"}

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_checkout_create)

    response = client.post(
        "/api/v1/billing/create-checkout-session",
        json={"org_id": 1, "plan_code": "PRO"},
    )

    assert response.status_code == 200
    assert response.json()["checkout_url"].startswith("https://stripe.test/checkout/pro")

    subscription = session.query(Subscription).filter_by(org_id=1).one()
    assert subscription.plan.code == "PRO"
    assert subscription.status == "pending"


def test_create_portal_session_requires_subscription(client, session, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test", raising=False)

    subscription = session.query(Subscription).filter_by(org_id=1).one()
    subscription.stripe_customer_id = "cus_test"
    session.add(subscription)
    session.commit()

    def fake_portal_create(**kwargs):
        assert kwargs["customer"] == "cus_test"
        return {"url": "https://stripe.test/portal"}

    monkeypatch.setattr(stripe.billing_portal.Session, "create", fake_portal_create)

    response = client.post(
        "/api/v1/billing/portal",
        json={"org_id": 1},
    )

    assert response.status_code == 200
    assert response.json()["portal_url"] == "https://stripe.test/portal"


def test_webhook_checkout_session_updates_subscription(client, session, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test", raising=False)
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test", raising=False)

    checkout_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"org_id": "1", "plan_code": "PRO"},
                "subscription": "sub_test",
                "customer": "cus_test",
            }
        },
    }

    def fake_construct_event(payload, signature, secret):
        assert secret == "whsec_test"
        return checkout_event

    def fake_subscription_retrieve(subscription_id):
        assert subscription_id == "sub_test"
        return {
            "id": subscription_id,
            "status": "active",
            "current_period_start": 1696118400,
            "current_period_end": 1698796800,
            "items": {
                "data": [
                    {"price": {"id": "price_test_pro"}},
                ]
            },
        }

    monkeypatch.setattr(stripe.Webhook, "construct_event", fake_construct_event)
    monkeypatch.setattr(stripe.Subscription, "retrieve", fake_subscription_retrieve)

    response = client.post(
        "/api/v1/billing/webhook",
        data="{}",
        headers={"Stripe-Signature": "sig_test"},
    )

    assert response.status_code == 200
    setting = session.query(OrgSetting).filter_by(org_id=1).one()
    assert setting.plan_features.get("exports_pdf") is True
    assert setting.plan_limits.get("max_xml_uploads_month") == 1000
    subscription = session.query(Subscription).filter_by(org_id=1).one()
    assert subscription.stripe_customer_id == "cus_test"
    assert subscription.status == "active"
