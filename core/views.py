from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.forms import ImageAssetUploadForm
from core.models import ImageAsset
from core.services.images import signed_image_url
from reviews.forms import ReviewForm
from reviews.models import Review, ReviewImage


def home(request):
    if request.method == "POST":
        form = ReviewForm(
            request.POST, request.FILES, allow_image_upload=settings.DEBUG
        )
        if form.is_valid():
            with transaction.atomic():  # type: ignore[reportGeneralTypeIssues]
                review = form.save()
                image = form.cleaned_data["image"]
                if image is not None:
                    asset = ImageAsset(
                        file=image,
                        alt_text=f"Photo of {review.dish_name}",
                    )
                    asset.full_clean()
                    asset.save()
                    ReviewImage.objects.create(review=review, image=asset)
                    ImageAsset.objects.filter(pk=asset.pk).update(
                        published_at=timezone.now()
                    )
            return redirect("home")
    else:
        form = ReviewForm(allow_image_upload=settings.DEBUG)

    review_images = Prefetch(
        "image_links",
        queryset=ReviewImage.objects.select_related("image").filter(
            image__deleted_at__isnull=True,
            image__published_at__isnull=False,
        ),
        to_attr="published_images",
    )
    reviews = list(
        Review.objects.prefetch_related(review_images)  # type: ignore[reportAttributeAccessIssue]
    )
    for review in reviews:
        for review_image in review.published_images:
            review_image.url = signed_image_url(review_image.image, None)

    return render(
        request,
        "core/home.html",
        {
            "form": form,
            "allow_image_upload": settings.DEBUG,
            "reviews": reviews,
        },
    )


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
