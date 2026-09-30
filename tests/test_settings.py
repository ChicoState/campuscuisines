from django.conf import settings


def test_production_proxy_header_is_configured() -> None:
    assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
