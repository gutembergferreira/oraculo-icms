from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.v1.routes import api_router
from app.core.config import settings
from app.logging import setup_logging

REQUEST_COUNT = Counter(
    "api_requests_total", "Total de requisições recebidas", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "Latência das requisições", ["endpoint"]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        with REQUEST_LATENCY.labels(endpoint=endpoint).time():
            response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        return response


def create_app() -> FastAPI:
    setup_logging.configure()

    app = FastAPI(
        title="Oráculo ICMS API",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        default_response_class=JSONResponse,
    )

    app.add_middleware(MetricsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/healthz", tags=["Observabilidade"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", tags=["Observabilidade"])
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
