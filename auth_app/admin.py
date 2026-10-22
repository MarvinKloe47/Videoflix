from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import User


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    """Manage email accounts using Django's standard permission and password UI."""

    form = UserChangeForm
    add_form = UserCreationForm
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_active", "is_staff", "is_superuser")
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": (
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
        )}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"fields": (
        "email", "usable_password", "password1", "password2",
    )}),)
