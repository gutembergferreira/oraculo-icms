FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


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
CMD ["uvicorn", "--app-dir", "/srv", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
