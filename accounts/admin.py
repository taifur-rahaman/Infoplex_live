from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "current_level", "interest", "phone")
    list_filter = ("role", "current_level")
    search_fields = ("user__username", "user__email", "phone")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
