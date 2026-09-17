"""Tests for configuration only; no product behavior belongs here."""

from scripts import verify_infrastructure


def test_infrastructure_verifier_passes() -> None:
    verify_infrastructure.main()
