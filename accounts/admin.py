from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .access import is_eligible_user
from .models import User


def eligible_admin_permission(request) -> bool:
    return is_eligible_user(request.user) and request.user.is_staff


admin.site.has_permission = eligible_admin_permission

admin.site.register(User, UserAdmin)
