from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ImageAsset

RETENTION_PERIOD = timedelta(days=30)


class Command(BaseCommand):
    help = "Permanently purge image assets soft deleted more than 30 days ago."

    def handle(self, *args, **options):
        cutoff = timezone.now() - RETENTION_PERIOD
        purged_count = 0
        assets = list(
            ImageAsset.all_objects.filter(deleted_at__lt=cutoff).only("pk", "file")
        )

        for asset in assets:
            try:
                if asset.file.name:
                    asset.file.storage.delete(asset.file.name)
                ImageAsset.all_objects.filter(
                    pk=asset.pk, deleted_at__lt=cutoff
                ).delete()
            except Exception:
                self.stderr.write(f"Failed to purge image asset {asset.pk}.")
            else:
                purged_count += 1

        suffix = "asset" if purged_count == 1 else "assets"
        self.stdout.write(f"Purged {purged_count} image {suffix}.")
