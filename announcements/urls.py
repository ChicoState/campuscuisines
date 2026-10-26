from django.urls import path

from announcements import views

urlpatterns = [
    path("announcements/history/", views.history, name="announcement-history"),
    path(
        "announcements/<int:pk>/dismiss/",
        views.dismiss,
        name="announcement-dismiss",
    ),
    path(
        "announcements/<int:pk>/reannounce/",
        views.reannounce,
        name="announcement-reannounce",
    ),
]
