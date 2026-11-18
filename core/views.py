from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.access import (
    eligible_login_required,
    is_eligible_user,
    redirect_to_eligible_login,
)
from catalog.forms import FoodItemForm
from catalog.models import MenuItem
from core.forms import ImageAssetUploadForm
from core.models import ImageAsset
from core.services.images import signed_image_url
from reviews.filters import (
    filter_reviews_by_selected_tag_ids,
    get_selected_tag_ids,
)
from reviews.forms import ReportForm, ReviewForm
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


def menu(request):
    if request.method == "POST":
        if not is_eligible_user(request.user):
            return redirect_to_eligible_login(request)
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.submitted_by = request.user
            food_item.save()
            form.save_m2m()
            return redirect("menu")
    else:
        form = FoodItemForm()
    return render(
        request,
        "core/map.html",
        {
            "form": form,
            "menu_items": MenuItem.objects.available_at(),
        },
    )


def about(request):
    return render(request, "core/about.html")


def account(request):
    return render(request, "core/account.html")


@eligible_login_required
@require_POST
def report_review(request, pk: int):
    review = get_object_or_404(Review, pk=pk)
    form = ReportForm(request.POST)
    if not form.is_valid():
        return redirect("reviews")

    report_type = form.cleaned_data["report_type"]
    target = {
        Report.REPORT_TYPE_REVIEW: {"review": review},
        Report.REPORT_TYPE_IMAGE: {},
        Report.REPORT_TYPE_ACCOUNT: {},
    }[report_type]
    review_image = (
        ReviewImage.objects.select_related("image__uploaded_by")
        .filter(
            review=review,
            image__deleted_at__isnull=True,
            image__published_at__isnull=False,
        )
        .first()
    )
    if report_type == Report.REPORT_TYPE_IMAGE:
        if review_image is None:
            return redirect("reviews")
        target = {"image": review_image.image}
    elif report_type == Report.REPORT_TYPE_ACCOUNT:
        if review_image is None or review_image.image.uploaded_by is None:
            return redirect("reviews")
        target = {"account": review_image.image.uploaded_by}

    report = Report(
        reporter=request.user,
        report_type=report_type,
        reason=form.cleaned_data["reason"],
        custom_reason=form.cleaned_data["custom_reason"],
        **target,
    )
    try:
        with transaction.atomic():  # type: ignore[reportGeneralTypeIssues]
            report.save()
    except IntegrityError:
        pass
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
        queryset=ReviewImage.objects.select_related("image__uploaded_by").filter(
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
