from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "full_name", "role", "position", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "full_name", "email")
    ordering = ("username",)
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("full_name", "role", "position", "phone")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("full_name", "role", "position")}),
    )
