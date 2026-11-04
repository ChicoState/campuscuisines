from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .access import is_eligible_user
from .models import User


def eligible_admin_permission(request) -> bool:
    return is_eligible_user(request.user) and request.user.is_staff


admin.site.has_permission = eligible_admin_permission


@admin.register(User)
class CampusUserAdmin(UserAdmin):
    """Keep account creation and privilege changes operator-only."""

    def has_module_permission(self, request) -> bool:
        return request.user.is_superuser and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser and super().has_view_permission(request, obj)

    def has_add_permission(self, request) -> bool:
        return request.user.is_superuser and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser and super().has_delete_permission(request, obj)
