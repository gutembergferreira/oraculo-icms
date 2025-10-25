from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenError(Exception):
    """Erro genérico para tokens inválidos."""


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.utcnow()
    to_encode: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def create_access_token(subject: str) -> str:
    return create_token(subject, timedelta(seconds=settings.jwt_access_expires), "access")


def create_refresh_token(subject: str, jti: Optional[str] = None) -> str:
    payload: dict[str, Any] = {"jti": jti} if jti else {}
    now = datetime.utcnow()
    expires = now + timedelta(seconds=settings.jwt_refresh_expires)
    base = {"sub": subject, "type": "refresh", "iat": now, "exp": expires}
    base.update(payload)
    return jwt.encode(base, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str, token_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError as exc:  # pragma: no cover - delegado para testes específicos
        raise TokenError("Token inválido") from exc

    if payload.get("type") != token_type:
        raise TokenError("Tipo de token inválido")
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
