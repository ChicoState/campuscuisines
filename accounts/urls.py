from allauth.socialaccount.providers.google.views import oauth2_callback, oauth2_login
from django.urls import path
from django.views.decorators.http import require_POST

from . import views

urlpatterns = [
    path("login/", views.login, name="account-login"),
    path("logout/", views.logout, name="account-logout"),
    path("google/login/", require_POST(oauth2_login), name="google_login"),
    path("google/login/callback/", oauth2_callback, name="google_callback"),
]
