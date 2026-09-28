# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

FROM base AS dependencies

COPY requirements.txt ./
RUN python -m pip install --prefix=/install --require-hashes -r requirements.txt

FROM base AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app
COPY --from=dependencies /install /usr/local
COPY --chown=app:app . ./
USER app
EXPOSE 8080

# Product implementation must provide the WSGI module. The image intentionally
# has no application entrypoint until that work begins.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} ${DJANGO_WSGI_MODULE:?Set DJANGO_WSGI_MODULE to your_project.wsgi}"]
