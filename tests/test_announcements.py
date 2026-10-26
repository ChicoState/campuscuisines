import pytest
from django.urls import reverse
from django.utils.crypto import get_random_string

from accounts.models import User
from announcements.models import Announcement, AnnouncementDismissal


@pytest.mark.django_db
def test_migration_seed_provides_test_announcement(client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert response.context["announcement_count"] == 1
    assert response.context["announcement_items"][0].title == "Test announcement"


@pytest.mark.django_db
def test_anonymous_dismissal_is_saved_and_removes_announcement(client) -> None:
    announcement = Announcement.objects.get(title="Test announcement")

    response = client.post(
        reverse("announcement-dismiss", args=[announcement.pk]),
        {"next": reverse("home")},
    )

    assert response.status_code == 302
    assert AnnouncementDismissal.objects.filter(
        announcement=announcement, session_key__isnull=False
    ).exists()
    assert client.get(reverse("home")).context["announcement_count"] == 0


@pytest.mark.django_db
def test_dismissal_does_not_follow_an_external_next_url(client) -> None:
    announcement = Announcement.objects.get(title="Test announcement")

    response = client.post(
        reverse("announcement-dismiss", args=[announcement.pk]),
        {"next": "https://example.com/phishing"},
    )

    assert response.url == reverse("home")


@pytest.mark.django_db
def test_authenticated_dismissal_is_saved_for_that_user_only(client) -> None:
    password = get_random_string(12)
    user = User.objects.create_user(username="announcer", password=password)
    other_user = User.objects.create_user(username="other", password=password)
    announcement = Announcement.objects.get(title="Test announcement")

    client.force_login(user)
    client.post(reverse("announcement-dismiss", args=[announcement.pk]))

    assert AnnouncementDismissal.objects.filter(
        announcement=announcement, user=user
    ).exists()
    assert client.get(reverse("home")).context["announcement_count"] == 0

    client.force_login(other_user)
    assert client.get(reverse("home")).context["announcement_count"] == 1


@pytest.mark.django_db
def test_history_page_lists_dismissed_and_inactive_announcements(client) -> None:
    Announcement.objects.create(
        title="Older announcement",
        author_name="Admin",
        body="Older body",
        is_active=False,
    )

    response = client.get(reverse("announcement-history"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Test announcement" in content
    assert "Older announcement" in content


@pytest.mark.django_db
def test_history_reannounce_action_is_only_available_to_staff(client) -> None:
    announcement = Announcement.objects.get(title="Test announcement")

    response = client.get(reverse("announcement-history"))

    assert response.status_code == 200
    assert (
        reverse("announcement-reannounce", args=[announcement.pk])
        not in response.content.decode()
    )

    user = User.objects.create_user(
        username="editor", password=get_random_string(12), is_staff=True
    )
    client.force_login(user)

    response = client.get(reverse("announcement-history"))

    assert (
        reverse("announcement-reannounce", args=[announcement.pk])
        in response.content.decode()
    )


@pytest.mark.django_db
def test_staff_can_reannounce_older_announcement_and_clear_dismissals(
    client,
) -> None:
    announcement = Announcement.objects.create(
        title="Older announcement",
        author_name="Admin",
        body="Older body",
        is_active=False,
    )
    user = User.objects.create_user(
        username="editor", password=get_random_string(12), is_staff=True
    )
    AnnouncementDismissal.objects.create(announcement=announcement, user=user)
    client.force_login(user)

    response = client.post(reverse("announcement-reannounce", args=[announcement.pk]))

    assert response.status_code == 302
    assert response.url == reverse("announcement-history")
    announcement.refresh_from_db()
    assert announcement.is_active is True
    assert not AnnouncementDismissal.objects.filter(announcement=announcement).exists()
    assert client.get(reverse("home")).context["announcement_count"] == 2


@pytest.mark.django_db
def test_non_staff_cannot_reannounce_an_announcement(client) -> None:
    announcement = Announcement.objects.get(title="Test announcement")

    response = client.post(reverse("announcement-reannounce", args=[announcement.pk]))

    assert response.status_code == 302
    assert response.url.startswith("/admin/login/")
    announcement.refresh_from_db()
    assert announcement.is_active is True
