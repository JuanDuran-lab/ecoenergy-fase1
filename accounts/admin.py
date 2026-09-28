from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "perfil EcoEnergy"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "get_organization",
        "get_groups",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_select_related = ("profile__organization",)

    @admin.display(description="organización")
    def get_organization(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.organization:
            return profile.organization
        return "Todas" if obj.is_superuser else "-"

    @admin.display(description="roles")
    def get_groups(self, obj):
        return ", ".join(group.name for group in obj.groups.all()) or "-"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "organization__name",
    )
    list_filter = ("organization",)
    ordering = ("user__username",)
    list_select_related = ("user", "organization")
