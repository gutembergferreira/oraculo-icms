from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_token
from app.db.session import SessionLocal
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.api_keys import verify_api_key

bearer_scheme = HTTPBearer(auto_error=True)
public_api_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db_session)],
) -> User:
    try:
        payload = decode_token(credentials.credentials, token_type="access")
    except TokenError as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo")
    return user


def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user


def get_active_api_key(
    api_key_header: Annotated[str | None, Depends(public_api_scheme)],
    db: Annotated[Session, Depends(get_db_session)],
) -> ApiKey:
    if not api_key_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key ausente")

    api_key = verify_api_key(db, token=api_key_header)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")
    db.commit()
    return api_key
