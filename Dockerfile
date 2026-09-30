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
# pip is only needed to build this image. Removing it keeps its vendored
# packages and packaging metadata out of the production runtime image.
RUN rm -rf \
    /usr/local/bin/pip \
    /usr/local/bin/pip3 \
    /usr/local/bin/pip3.13 \
    /usr/local/lib/python3.13/site-packages/pip \
    /usr/local/lib/python3.13/site-packages/pip-*.dist-info
RUN install --directory --owner=app --group=app /app/staticfiles
USER app
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY="$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(48))')" \
    python manage.py collectstatic --noinput
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} config.wsgi"]
