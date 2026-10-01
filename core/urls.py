from django.urls import path

from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("images/upload/", views.image_upload, name="image-upload"),
    path("images/<int:pk>/", views.image_detail, name="image-detail"),
]
