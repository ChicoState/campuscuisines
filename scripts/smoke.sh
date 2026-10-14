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

docker compose run --rm --no-deps minio-init >/dev/null
docker compose exec -T \
  -e "OBJECT_STORAGE_BUCKET=${OBJECT_STORAGE_BUCKET:-campus-cuisines-uploads}" \
  minio sh -ec '
  mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  case "$(mc anonymous get local/"$OBJECT_STORAGE_BUCKET")" in
    *private*) ;;
    *) exit 1 ;;
  esac
'

echo "PostgreSQL and private MinIO bucket passed infrastructure readiness checks."
