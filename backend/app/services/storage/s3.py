from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import Iterable
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.services.storage.base import StoredObject, StorageBackend


class S3StorageBackend(StorageBackend):
    name = "s3"

    def __init__(self) -> None:
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET não configurado para backend s3/minio")
        if not settings.s3_access_key or not settings.s3_secret_key:
            raise RuntimeError("Credenciais S3 não configuradas para backend s3/minio")
        self.bucket = settings.s3_bucket
        self.client = _SimpleS3Client(
            endpoint_url=(
                str(settings.s3_endpoint_url) if settings.s3_endpoint_url else None
            ),
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region=settings.s3_region,
            use_ssl=settings.s3_secure,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.create_bucket(self.bucket)

    def store(
        self,
        *,
        org_id: int,
        file_name: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        safe_name = file_name.replace("/", "_")
        object_key = f"org-{org_id}/{timestamp}_{safe_name}"
        self.client.put_object(
            bucket=self.bucket,
            key=object_key,
            data=content,
            content_type=content_type,
        )
        return StoredObject(
            path=object_key,
            content_type=content_type,
            size=len(content),
        )

    def read(self, *, path: str) -> bytes:
        return self.client.get_object(bucket=self.bucket, key=path)


class _SimpleS3Client:
    """Cliente mínimo compatível com S3 usando assinatura SigV4."""

    def __init__(
        self,
        *,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        region: str | None,
        use_ssl: bool,
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region or "us-east-1"
        base_url = self._resolve_base_url(endpoint_url, use_ssl)
        self._base_url = httpx.URL(base_url)
        if self._base_url.path not in ("", "/"):
            raise RuntimeError("S3 endpoint não deve conter caminho extra")
        verify = use_ssl if self._base_url.scheme == "https" else False
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(30.0),
            verify=verify,
        )
        self._host_header = self._client.base_url.netloc

    def bucket_exists(self, bucket: str) -> bool:
        response = self._request(
            "HEAD",
            bucket=bucket,
            allowed_statuses={200, 301, 302, 403, 404},
        )
        if response.status_code == 404:
            return False
        return True

    def create_bucket(self, bucket: str) -> None:
        body: bytes = b""
        headers: dict[str, str] = {}
        if self.region and self.region != "us-east-1":
            body = (
                "<CreateBucketConfiguration "
                "xmlns=\"http://s3.amazonaws.com/doc/2006-03-01/\">"
                f"<LocationConstraint>{self.region}</LocationConstraint>"
                "</CreateBucketConfiguration>"
            ).encode("utf-8")
            headers["content-type"] = "application/xml"
        self._request(
            "PUT",
            bucket=bucket,
            data=body,
            headers=headers,
            allowed_statuses={200, 204},
        )

    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str | None,
    ) -> None:
        headers: dict[str, str] = {}
        if content_type:
            headers["content-type"] = content_type
        self._request(
            "PUT",
            bucket=bucket,
            key=key,
            data=data,
            headers=headers,
            allowed_statuses={200},
        )

    def get_object(self, *, bucket: str, key: str) -> bytes:
        response = self._request(
            "GET",
            bucket=bucket,
            key=key,
            allowed_statuses={200},
        )
        return response.content

    def _resolve_base_url(self, endpoint_url: str | None, use_ssl: bool) -> str:
        if endpoint_url:
            return endpoint_url.rstrip("/")
        scheme = "https" if use_ssl else "http"
        host = f"s3.{self.region}.amazonaws.com"
        return f"{scheme}://{host}"

    def _request(
        self,
        method: str,
        *,
        bucket: str,
        key: str | None = None,
        data: bytes | str | None = None,
        headers: dict[str, str] | None = None,
        allowed_statuses: Iterable[int] | None = None,
    ) -> httpx.Response:
        body = self._coerce_body(data)
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        headers.setdefault("host", self._host_header)
        headers.setdefault("content-length", str(len(body)))
        canonical_uri = self._build_canonical_uri(bucket=bucket, key=key)
        canonical_query = ""
        payload_hash = hashlib.sha256(body).hexdigest()
        amz_date = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        headers["x-amz-date"] = amz_date
        headers["x-amz-content-sha256"] = payload_hash
        canonical_headers = "".join(
            f"{k}:{headers[k].strip()}\n" for k in sorted(headers)
        )
        signed_headers = ";".join(sorted(headers))
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_query}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )
        credential_scope = f"{amz_date[:8]}/{self.region}/s3/aws4_request"
        string_to_sign = (
            "AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        signing_key = self._signature_key(amz_date[:8])
        signature = hmac.new(
            signing_key,
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers["authorization"] = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        request_path = canonical_uri
        if canonical_query:
            request_path = f"{canonical_uri}?{canonical_query}"
        response = self._client.request(
            method,
            request_path,
            headers=headers,
            content=body,
        )
        allowed = set(allowed_statuses or {200})
        if response.status_code not in allowed:
            detail = response.text[:200]
            raise RuntimeError(
                f"Erro ao comunicar com S3 ({response.status_code}): {detail}"
            )
        return response

    def _build_canonical_uri(self, *, bucket: str, key: str | None) -> str:
        encoded = quote(bucket, safe="-_.~")
        if key:
            key_encoded = quote(key, safe="/-_.~")
            return f"/{encoded}/{key_encoded}"
        return f"/{encoded}"

    def _coerce_body(self, data: bytes | str | None) -> bytes:
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        return data.encode("utf-8")

    def _signature_key(self, datestamp: str) -> bytes:
        key_date = hmac.new(
            ("AWS4" + self.secret_key).encode("utf-8"),
            datestamp.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        key_region = hmac.new(
            key_date,
            self.region.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        key_service = hmac.new(key_region, b"s3", hashlib.sha256).digest()
        return hmac.new(key_service, b"aws4_request", hashlib.sha256).digest()
