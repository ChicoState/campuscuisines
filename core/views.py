from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.access import (
    eligible_login_required,
    is_eligible_user,
    redirect_to_eligible_login,
)
from catalog.models import MenuItem
from core.forms import ImageAssetUploadForm
from core.models import ImageAsset
from core.services.images import signed_image_url
from reviews.filters import (
    filter_reviews_by_selected_tag_ids,
    get_selected_tag_ids,
)
from reviews.forms import ReviewForm
from reviews.models import Report, Review, ReviewImage


def home(request):
    if request.method == "POST" and not is_eligible_user(request.user):
        return redirect_to_eligible_login(request)

    if request.method == "POST":
        return _handle_review_submission(request)

    reviews = _reviews_with_images()[:3]
    return render(
        request,
        "core/home.html",
        {
            "reviews": reviews,
        },
    )


def reviews(request):
    if request.method == "POST":
        if not is_eligible_user(request.user):
            return redirect_to_eligible_login(request)
        return _handle_review_submission(request)

    selected_review_tag_ids = get_selected_tag_ids(request.GET.getlist("review_tag"))
    return render(
        request,
        "core/reviews.html",
        {
            "form": ReviewForm(allow_image_upload=settings.DEBUG),
            "allow_image_upload": settings.DEBUG,
            "menu_items": MenuItem.objects.order_by("name", "id"),
            "reviews": _reviews_with_images(selected_review_tag_ids),
            "selected_review_tag_ids": selected_review_tag_ids,
        },
    )


def images(request):
    image_items = [
        {"asset": asset, "url": signed_image_url(asset, request.user)}
        for asset in ImageAsset.objects.filter(published_at__isnull=False)
    ]
    return render(
        request,
        "core/images.html",
        {"image_items": image_items, "allow_image_upload": settings.DEBUG},
    )


def map_locations(request):
    return render(request, "core/map.html")


def about(request):
    return render(request, "core/about.html")


def account(request):
    return render(request, "core/account.html")


@eligible_login_required
@require_POST
def report_review(request, pk: int):
    review = get_object_or_404(Review, pk=pk)
    Report.objects.get_or_create(reporter=request.user, review=review)
    return redirect("reviews")


def _handle_review_submission(request, template_name="core/reviews.html"):
    form = ReviewForm(request.POST, request.FILES, allow_image_upload=settings.DEBUG)
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
        return redirect("reviews")

    return render(
        request,
        template_name,
        {
            "form": form,
            "allow_image_upload": settings.DEBUG,
            "menu_items": MenuItem.objects.order_by("name", "id"),
            "reviews": _reviews_with_images(),
        },
    )


def _reviews_with_images(selected_review_tag_ids: set[int] | None = None):
    review_images = Prefetch(
        "image_links",
        queryset=ReviewImage.objects.select_related("image").filter(
            image__deleted_at__isnull=True,
            image__published_at__isnull=False,
        ),
        to_attr="published_images",
    )
    selected_review_tag_ids = selected_review_tag_ids or set()
    reviews = list(
        filter_reviews_by_selected_tag_ids(
            Review.objects.prefetch_related(review_images), selected_review_tag_ids
        )  # type: ignore[reportAttributeAccessIssue]
    )
    for review in reviews:
        for review_image in review.published_images:
            review_image.url = signed_image_url(review_image.image, None)
    return reviews


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
