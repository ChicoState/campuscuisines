from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render

from core.forms import ImageAssetUploadForm


def home(request):
    return render(request, "core/home.html")


def image_upload(request):
    if not settings.DEBUG and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    if request.method == "POST":
        form = ImageAssetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            if request.user.is_authenticated:
                asset.uploaded_by = request.user
            asset.save()
            return redirect("image-upload")
    else:
        form = ImageAssetUploadForm()

    return render(request, "core/image_upload.html", {"form": form})
