from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render

from core.forms import ImageAssetUploadForm
from core.models import ImageAsset
from core.services.images import signed_image_url


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
            if asset.uploaded_by_id is not None:
                return redirect("image-detail", pk=asset.pk)
            return redirect("image-upload")
    else:
        form = ImageAssetUploadForm()

    return render(request, "core/image_upload.html", {"form": form})


@login_required
def image_detail(request, pk: int):
    asset = get_object_or_404(ImageAsset, pk=pk)
    return render(
        request,
        "core/image_detail.html",
        {"asset": asset, "image_url": signed_image_url(asset, request.user)},
    )
