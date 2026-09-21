#!/usr/bin/env sh
set -eu

cleanup() {
  docker compose down --volumes --remove-orphans
}

trap cleanup EXIT INT TERM

python3 scripts/verify_infrastructure.py
docker compose config >/dev/null
docker compose up -d postgres minio

until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-campuscuisines}" -d "${POSTGRES_DB:-campuscuisines}" >/dev/null; do
  sleep 1
done

until docker compose exec -T minio curl --fail --silent http://localhost:9000/minio/health/live >/dev/null; do
  sleep 1
done

echo "PostgreSQL and MinIO passed infrastructure readiness checks."
