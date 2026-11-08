"""Top-level URL configuration."""

from django.contrib import admin
from django.urls import include, path

from accounts.views import admin_login

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("admin/login/", admin_login, name="admin-login"),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
