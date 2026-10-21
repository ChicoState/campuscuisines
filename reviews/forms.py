from itertools import groupby

from django import forms
from django.core.exceptions import ValidationError

from core.validators import validate_raster_image

from .models import Review, Tag

RATING_CHOICES = [
    (1, "1 out of 5 stars — Bad"),
    (2, "2 out of 5 stars — Mediocre"),
    (3, "3 out of 5 stars — Fine"),
    (4, "4 out of 5 stars — Good"),
    (5, "5 out of 5 stars — Amazing"),
]


class ReviewForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"}
        ),
    )

    def __init__(self, *args, allow_image_upload: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.allow_image_upload = allow_image_upload
        tags = Tag.objects.select_related("category")
        self.fields["tags"].queryset = tags
        self.tag_groups = [
            {
                "name": category_name,
                "tags": list(category_tags),
            }
            for category_name, category_tags in groupby(
                tags, key=lambda tag: tag.category.name
            )
        ]
        selected_tags = self["tags"].value() or []
        selected_tag_ids = {str(tag_id) for tag_id in selected_tags}
        self.selected_tag_ids = {
            str(tag.pk)
            for group in self.tag_groups
            for tag in group["tags"]
            if str(tag.pk) in selected_tag_ids
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image is None:
            return None
        if not self.allow_image_upload:
            raise ValidationError(
                "Image uploads are only available in local debug mode."
            )
        validate_raster_image(image)
        return image

    class Meta:
        model = Review
        fields = ["dish_name", "reviewer_name", "rating", "text", "tags"]
        widgets = {
            "dish_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "reviewer_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "rating": forms.RadioSelect(choices=RATING_CHOICES),
            "text": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "dish_name": "Dish name",
            "reviewer_name": "Your name",
            "rating": "Your rating",
            "text": "Your review",
            "tags": "Applicable tags",
        }
