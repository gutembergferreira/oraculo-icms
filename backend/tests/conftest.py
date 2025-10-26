from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import session as db_session
from app.db.base_class import Base
import app.db.base  # noqa: F401
from app.main import app
from app.models.organization import Organization
from app.models.org_setting import OrgSetting
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_org_role import UserOrgRole


@pytest.fixture()
def engine() -> Iterator:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    assert "files" in Base.metadata.tables
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def session(engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    SessionTesting = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "SessionLocal", SessionTesting)
    import app.api.deps as deps_module
    monkeypatch.setattr(deps_module, "SessionLocal", SessionTesting)
    import app.workers.tasks as tasks_module
    monkeypatch.setattr(tasks_module, "SessionLocal", SessionTesting)
    settings.local_storage_path = str(tmp_path / "storage")
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def seed_data(session):
    plan_free = Plan(
        code="FREE",
        name="Free",
        monthly_price_cents=0,
        features={"exports_pdf": False, "exports_xlsx": False},
        limits={"max_xml_uploads_month": 100, "max_storage_mb": 256, "max_users": 3},
    )
    plan_pro = Plan(
        code="PRO",
        name="Pro",
        monthly_price_cents=49900,
        features={"exports_pdf": True, "exports_xlsx": True},
        limits={"max_xml_uploads_month": 1000, "max_storage_mb": 4096, "max_users": 10},
        stripe_product_id="prod_test_pro",
        stripe_price_id="price_test_pro",
    )
    session.add_all([plan_free, plan_pro])
    session.flush()

    org = Organization(name="Org Teste", slug="org-teste", cnpj="12345678000199")
    session.add(org)
    session.flush()

    setting = OrgSetting(
        id=org.id,
        org_id=org.id,
        current_plan_id=plan_free.id,
        plan_limits=plan_free.limits,
        plan_features=plan_free.features,
    )
    session.add(setting)

    subscription = Subscription(org_id=org.id, plan_id=plan_free.id, status="active")
    session.add(subscription)

    user = User(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password_hash="hashed",
    )
    session.add(user)
    session.flush()

    relation = UserOrgRole(id=user.id, user_id=user.id, org_id=org.id, role="owner")
    session.add(relation)
    session.commit()

    return user, org


@pytest.fixture()
def client(session, seed_data):
    user, _ = seed_data

    def _override_user():
        return user

    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
