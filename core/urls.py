from django.urls import path

from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/<int:pk>/report/", views.report_review, name="report-review"),
    path("images/", views.images, name="images"),
    path("images/upload/", views.image_upload, name="image-upload"),
    path("images/<int:pk>/", views.image_detail, name="image-detail"),
    path("map/", views.menu, name="map"),
    path("menu/", views.menu, name="menu"),
    path("about/", views.about, name="about"),
    path("account/", views.account, name="account"),
]
