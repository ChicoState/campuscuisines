from django import forms

from .models import Review

RATING_CHOICES = [
    (1, "1 out of 5 stars — Bad"),
    (2, "2 out of 5 stars — Mediocre"),
    (3, "3 out of 5 stars — Fine"),
    (4, "4 out of 5 stars — Good"),
    (5, "5 out of 5 stars — Amazing"),
]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["dish_name", "reviewer_name", "rating", "text"]
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
        }
