from django import forms

from core.models import ImageAsset


class ImageAssetUploadForm(forms.ModelForm):
    class Meta:
        model = ImageAsset
        fields = ["file", "alt_text", "caption"]
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                }
            ),
        }
