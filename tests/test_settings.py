from django.conf import settings


def test_production_proxy_header_is_configured() -> None:
    assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_default_media_storage_uses_private_s3_compatible_storage() -> None:
    default_storage = settings.STORAGES["default"]

    assert default_storage["BACKEND"] == "storages.backends.s3.S3Storage"
    assert default_storage["OPTIONS"]["bucket_name"] == "campus-cuisines-uploads"
    assert default_storage["OPTIONS"]["default_acl"] is None
    assert default_storage["OPTIONS"]["querystring_auth"] is True
    assert default_storage["OPTIONS"]["addressing_style"] == "path"
