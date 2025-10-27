from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.api_key import ApiKey


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(session: Session, *, org_id: int, name: str) -> tuple[ApiKey, str]:
    token = secrets.token_urlsafe(32)
    prefix = token[:12]
    hashed = _hash_key(token)
    api_key = ApiKey(
        org_id=org_id,
        name=name,
        prefix=prefix,
        hashed_key=hashed,
    )
    session.add(api_key)
    session.flush()
    return api_key, token


def verify_api_key(session: Session, *, token: str) -> ApiKey | None:
    if "=" in token:
        token = token.split("=")[-1]
    prefix = token[:12]
    hashed = _hash_key(token)
    api_key = (
        session.query(ApiKey)
        .filter(ApiKey.prefix == prefix, ApiKey.is_active.is_(True))
        .one_or_none()
    )
    if api_key and api_key.hashed_key == hashed:
        api_key.last_used_at = datetime.utcnow()
        session.add(api_key)
        session.flush()
        return api_key
    return None
