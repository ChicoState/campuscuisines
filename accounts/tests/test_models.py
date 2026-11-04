import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.models import User


@pytest.mark.django_db
def test_user_email_is_required_and_case_normalized() -> None:
    user = User.objects.create_user(
        username="student", email="Student@CSUCHICO.EDU", password="unused"
    )

    assert user.email == "student@csuchico.edu"


@pytest.mark.django_db
def test_user_email_is_unique() -> None:
    User.objects.create_user(
        username="first", email="student@csuchico.edu", password="unused"
    )

    with pytest.raises(IntegrityError):
        User.objects.create_user(
            username="second", email="student@csuchico.edu", password="unused"
        )


def test_user_without_email_cannot_be_saved() -> None:
    with pytest.raises(ValueError, match="email identity is required"):
        User(username="student").save()


@pytest.mark.django_db
def test_email_cannot_be_changed_after_creation() -> None:
    user = User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )
    user.email = "new-student@csuchico.edu"

    with pytest.raises(ValueError, match="email identity is immutable"):
        user.save()


@pytest.mark.django_db
def test_email_model_validation_is_not_replaced_by_save_guard() -> None:
    user = User(username="student", email="not-an-email")

    with pytest.raises(ValidationError):
        user.full_clean()
