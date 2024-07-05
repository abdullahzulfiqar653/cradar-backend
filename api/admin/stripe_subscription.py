from django.contrib import admin

from api.models.stripe_subscription import StripeSubscription


@admin.register(StripeSubscription)
class StripeSubscriptionAdmin(admin.ModelAdmin):
    list_filter = ("status", "is_free_trial")
    list_display = (
        "id",
        "workspace",
        "product",
        "user",
        "started_at",
        "end_at",
        "status",
        "is_free_trial",
    )
    search_fields = (
        "id",
        "workspace__name",
        "product__name",
        "user__username",
        "user__email",
    )
    readonly_fields = ["id"]
    ordering = ("-started_at",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("workspace", "product", "user")
        return queryset

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
