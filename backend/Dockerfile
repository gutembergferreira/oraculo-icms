FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libpq-dev \
    libcairo2 libpangocairo-1.0-0 libpango-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 libglib2.0-0 libharfbuzz0b \
    libjpeg62-turbo libpng16-16 libfreetype6 \
    shared-mime-info fonts-dejavu-core fonts-liberation \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /srv

# 1) deps Poetry (aproveita cache)
COPY pyproject.toml poetry.lock* /srv/
RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# 2) código do backend
COPY . /srv

# 3) instala o projeto em si (inclui o pacote "app")
RUN poetry install --no-interaction --no-ansi

# 4) garanta que /srv está no path de import
ENV PYTHONPATH=/srv

# 5) rode apontando explicitamente o diretório
CMD ["sh","-lc","alembic upgrade head && uvicorn --app-dir /srv app.main:app --host 0.0.0.0 --port 8000"]

