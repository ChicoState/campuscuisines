from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from secrets import token_urlsafe

from django.conf import settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def settings_import(*, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", "from config.settings import DEBUG; print(DEBUG)"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_debug_defaults_to_false_when_django_debug_is_unset() -> None:
    environment = os.environ.copy()
    environment.pop("DJANGO_DEBUG", None)
    environment["DJANGO_SECRET_KEY"] = token_urlsafe(32)

    result = settings_import(environment=environment)

    assert result.returncode == 0
    assert result.stdout.strip() == "False"


def test_non_debug_startup_requires_an_explicit_secret_key() -> None:
    environment = os.environ.copy()
    environment.pop("DJANGO_DEBUG", None)
    environment.pop("DJANGO_SECRET_KEY", None)

    result = settings_import(environment=environment)

    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false." in result.stderr


def test_django_debug_true_is_an_explicit_opt_in() -> None:
    environment = os.environ.copy()
    environment["DJANGO_DEBUG"] = "true"
    environment.pop("DJANGO_SECRET_KEY", None)

    result = settings_import(environment=environment)

    assert result.returncode == 0
    assert result.stdout.strip() == "True"


def test_compose_does_not_default_django_debug_to_true() -> None:
    compose_file = (PROJECT_ROOT / "compose.yml").read_text()

    assert "DJANGO_DEBUG: ${DJANGO_DEBUG:-false}" in compose_file


def test_production_proxy_header_is_configured() -> None:
    assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_default_media_storage_uses_private_s3_compatible_storage() -> None:
    default_storage = settings.STORAGES["default"]

    assert default_storage["BACKEND"] == "storages.backends.s3.S3Storage"
    assert default_storage["OPTIONS"]["bucket_name"] == "campus-cuisines-uploads"
    assert default_storage["OPTIONS"]["default_acl"] is None
    assert default_storage["OPTIONS"]["querystring_auth"] is True
    assert default_storage["OPTIONS"]["addressing_style"] == "path"
