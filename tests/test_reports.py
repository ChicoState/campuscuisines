from typing import cast

import pytest
from django.db import IntegrityError
from django.urls import reverse

from accounts.models import User
from reviews.models import Report, Review

pytestmark = pytest.mark.django_db


def create_review() -> Review:
    return Review.objects.create(
        dish_name="Mushroom ramen",
        reviewer_name="Avery",
        rating=4,
        text="Warm, savory, and excellent.",
    )


def create_user(email: str = "student@csuchico.edu") -> User:
    return User.objects.create_user(
        username=email.split("@", maxsplit=1)[0], email=email, password="unused"
    )


def test_report_stores_reporter_and_review() -> None:
    report = Report(reporter=create_user(), review=create_review())

    report.full_clean()
    assert cast(User, report.reporter).email == "student@csuchico.edu"
    assert cast(Review, report.review).dish_name == "Mushroom ramen"


def test_report_database_constraint_prevents_duplicate_reporter_review_pair() -> None:
    reporter = create_user()
    review = create_review()
    Report.objects.create(reporter=reporter, review=review)

    with pytest.raises(IntegrityError):
        Report.objects.create(reporter=reporter, review=review)


def test_authenticated_user_can_report_a_review(client) -> None:
    reporter = create_user()
    review = create_review()
    client.force_login(reporter)

    response = client.post(reverse("report-review", args=[review.pk]))

    assert response.status_code == 302
    assert response.url == reverse("reviews")
    report = Report.objects.get()
    assert report.reporter == reporter
    assert report.review == review


def test_anonymous_user_cannot_report_a_review(client) -> None:
    review = create_review()

    response = client.post(reverse("report-review", args=[review.pk]))

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next=/reviews/{review.pk}/report/"
    assert not Report.objects.exists()


def test_duplicate_report_is_handled_without_creating_another_report(client) -> None:
    reporter = create_user()
    review = create_review()
    Report.objects.create(reporter=reporter, review=review)
    client.force_login(reporter)

    response = client.post(reverse("report-review", args=[review.pk]))

    assert response.status_code == 302
    assert Report.objects.count() == 1


def test_report_requires_post(client) -> None:
    reporter = create_user()
    review = create_review()
    client.force_login(reporter)

    response = client.get(reverse("report-review", args=[review.pk]))

    assert response.status_code == 405
    assert not Report.objects.exists()


def test_report_requires_csrf_token() -> None:
    from django.test import Client

    reporter = create_user()
    review = create_review()
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(reporter)

    response = csrf_client.post(reverse("report-review", args=[review.pk]))

    assert response.status_code == 403  # type: ignore[reportAttributeAccessIssue]
    assert not Report.objects.exists()


def test_reviews_page_has_a_confirmed_report_form(client) -> None:
    review = create_review()
    client.force_login(create_user())

    response = client.get(reverse("reviews"))

    assert response.status_code == 200
    content = response.content.decode()
    assert reverse("report-review", args=[review.pk]) in content
    assert "confirm(" in content
