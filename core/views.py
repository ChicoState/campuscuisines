from django.shortcuts import redirect, render

from reviews.forms import ReviewForm
from reviews.models import Review


def home(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ReviewForm()

    return render(
        request,
        "core/home.html",
        {
            "form": form,
            "reviews": Review.objects.all(),  # type: ignore[reportAttributeAccessIssue]
        },
    )
