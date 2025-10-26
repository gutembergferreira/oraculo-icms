from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.core.config import settings


class SSOConfigurationError(RuntimeError):
    """Erro para configurações inválidas de SSO."""


class SSOClient:
    def __init__(self) -> None:
        if not settings.sso_enabled:
            raise SSOConfigurationError("SSO não habilitado")
        required = [
            settings.sso_client_id,
            settings.sso_client_secret,
            settings.sso_authorize_url,
            settings.sso_token_url,
        ]
        if any(value is None for value in required):
            raise SSOConfigurationError("Configuração de SSO incompleta")
        self.client_id = settings.sso_client_id
        self.client_secret = settings.sso_client_secret
        self.authorize_url = str(settings.sso_authorize_url)
        self.token_url = str(settings.sso_token_url)
        self.userinfo_url = (
            str(settings.sso_userinfo_url) if settings.sso_userinfo_url else None
        )
        self.redirect_uri = (
            str(settings.sso_redirect_uri) if settings.sso_redirect_uri else None
        )
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    def build_authorization_url(self, state: str) -> str:
        query = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        if self.redirect_uri:
            query["redirect_uri"] = self.redirect_uri
        return f"{self.authorize_url}?{urlencode(query)}"

    def exchange_code(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()

    def fetch_userinfo(self, access_token: str) -> dict:
        if not self.userinfo_url:
            raise SSOConfigurationError("URL de userinfo não configurada")
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()
