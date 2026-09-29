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
RUN install --directory --owner=app --group=app /app/staticfiles
USER app
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY="$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(48))')" \
    python manage.py collectstatic --noinput
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} config.wsgi"]
