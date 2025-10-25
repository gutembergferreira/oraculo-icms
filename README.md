# Oráculo ICMS

Plataforma SaaS multiempresa para auditoria fiscal de XMLs de NF-e.

## Visão Geral

O projeto "Oráculo ICMS" é uma solução completa para ingestão, análise e auditoria de documentos fiscais eletrônicos (NF-e) com foco em conformidade tributária brasileira. A aplicação fornece upload e parsing de XMLs, motor de regras com sugestões de ajustes e relatórios técnicos/gerenciais, além de gestão de planos com Stripe.

### Roadmap Interno

- **v0.1**: Upload/parse/consulta.
- **v0.2**: Auditoria baseline + relatórios.
- **v0.3**: Planos/Stripe.
- **v0.4**: Editor de regras (DSL) e ZFM pack.
- **v1.0**: API pública + MinIO + SSO opcional.

## Estrutura do Repositório

- `backend/`: Aplicação FastAPI, modelos SQLAlchemy, serviços, workers Celery e migrações Alembic.
- `frontend/`: Aplicação React + Vite + Tailwind + shadcn/ui.
- `infrastructure/`: Arquivos Docker, Nginx/Traefik e configurações de deploy.
- `docs/`: Guias funcionais e técnicos, inclusive especificações de regras e Stripe.
- `.github/workflows`: Pipelines CI/CD com lint, testes e build.

## Executando com Docker Compose

1. Copie o arquivo `.env.example` para `.env` e ajuste as variáveis.
2. Execute `docker compose -f infrastructure/docker-compose.dev.yml up --build`.
3. Acesse a aplicação web em `http://localhost:3000` e a API em `http://localhost:8000`.

## Licença

MIT.
