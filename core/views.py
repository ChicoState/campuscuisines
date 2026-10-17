from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.access import (
    eligible_login_required,
    is_eligible_user,
    redirect_to_eligible_login,
)
from core.forms import ImageAssetUploadForm
from core.models import ImageAsset
from core.services.images import signed_image_url
from reviews.forms import ReviewForm
from reviews.models import Review, ReviewImage


def home(request):
    if request.method == "POST" and not is_eligible_user(request.user):
        return redirect_to_eligible_login(request)

    can_submit = is_eligible_user(request.user)
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
        form = ReviewForm(allow_image_upload=settings.DEBUG) if can_submit else None

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
            "allow_image_upload": settings.DEBUG and can_submit,
            "can_submit": can_submit,
            "reviews": reviews,
        },
    )


@eligible_login_required
def image_upload(request):
    if request.method == "POST":
        form = ImageAssetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.uploaded_by = request.user
            asset.save()
            return redirect("image-detail", pk=asset.pk)
    else:
        form = ImageAssetUploadForm()

    return render(request, "core/image_upload.html", {"form": form})


@eligible_login_required
def image_detail(request, pk: int):
    asset = get_object_or_404(ImageAsset, pk=pk)
    return render(
        request,
        "core/image_detail.html",
        {"asset": asset, "image_url": signed_image_url(asset, request.user)},
    )
