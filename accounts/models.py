from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A Google-identity-backed campus account."""

    email = models.EmailField("email address", unique=True, blank=False, editable=False)

    def save(self, *args, **kwargs):
        if not self.email:
            raise ValueError("email identity is required")

        self.email = str(self.email).strip().lower()
        if self.pk:
            current_email = type(self).objects.only("email").get(pk=self.pk).email
            if current_email != self.email:
                raise ValueError("email identity is immutable")
        return super().save(*args, **kwargs)
